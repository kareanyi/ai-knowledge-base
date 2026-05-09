"""Publisher 模块 - 多渠道内容分发。

支持 Telegram Bot API 和飞书 Webhook 两种渠道，
提供统一的异步发布接口。
"""

import asyncio
import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    """单次发布结果记录。

    Attributes:
        channel: 渠道名称（telegram / feishu）。
        success: 发布是否成功。
        message_id: 渠道返回的消息 ID，失败时为 None。
        error: 错误信息，成功时为 None。
    """

    channel: str
    success: bool
    message_id: str | None = None
    error: str | None = None


class BasePublisher(ABC):
    """内容发布器的抽象基类。

    定义 send_message() 和 send_digest() 两个标准接口，
    所有渠道publisher必须实现这两个方法。
    """

    @abstractmethod
    async def send_message(self, content: str, **kwargs: Any) -> PublishResult:
        """发送单条消息。

        Args:
            content: 消息内容。
            **kwargs: 渠道特定的额外参数。

        Returns:
            PublishResult 包含发布结果。
        """

    @abstractmethod
    async def send_digest(self, content: str, **kwargs: Any) -> PublishResult:
        """发送知识日报/摘要。

        Args:
            content: 日报内容。
            **kwargs: 渠道特定的额外参数。

        Returns:
            PublishResult 包含发布结果。
        """


class TelegramPublisher(BasePublisher):
    """Telegram 渠道发布器。

    通过 Telegram Bot API 异步发送 MarkdownV2 格式消息。
    环境变量:
        TELEGRAM_BOT_TOKEN: Bot 访问令牌。
        TELEGRAM_CHAT_ID: 目标聊天 ID。
    """

    _TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
    _TIMEOUT_SECONDS = 30.0

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None) -> None:
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        if not self.bot_token or not self.chat_id:
            logger.warning("TelegramPublisher: TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 未设置")

    async def send_message(self, content: str, **kwargs: Any) -> PublishResult:
        """通过 Telegram Bot API 发送 MarkdownV2 消息。

        Args:
            content: MarkdownV2 格式消息文本。
            **kwargs: 支持 parse_mode="MarkdownV2"（默认）及 chat_id 覆盖。

        Returns:
            PublishResult。
        """
        parse_mode = kwargs.get("parse_mode", "MarkdownV2")
        chat_id = kwargs.get("chat_id", self.chat_id)
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": content,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        return await self._post(payload)

    async def send_digest(self, content: str, **kwargs: Any) -> PublishResult:
        """通过 Telegram 发送知识日报。

        Args:
            content: MarkdownV2 格式日报文本。
            **kwargs: 同 send_message。

        Returns:
            PublishResult。
        """
        return await self.send_message(content, **kwargs)

    async def _post(self, payload: dict[str, Any]) -> PublishResult:
        """向 Telegram Bot API 发送 POST 请求。

        Args:
            payload: 请求体字典。

        Returns:
            PublishResult。
        """
        url = self._TELEGRAM_API_URL.format(token=self.bot_token)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._TIMEOUT_SECONDS),
                ) as response:
                    data = await response.json()
                    if response.status == 200 and data.get("ok"):
                        msg_id = str(data.get("result", {}).get("message_id", ""))
                        logger.info("Telegram 消息发送成功，message_id=%s", msg_id)
                        return PublishResult(channel="telegram", success=True, message_id=msg_id)
                    error_desc = data.get("description", f"HTTP {response.status}")
                    logger.warning("Telegram 消息发送失败: %s", error_desc)
                    return PublishResult(channel="telegram", success=False, error=error_desc)
        except aiohttp.ClientError as e:
            logger.error("Telegram 请求异常: %s", e)
            return PublishResult(channel="telegram", success=False, error=str(e))
        except TimeoutError as e:
            logger.error("Telegram 请求超时: %s", e)
            return PublishResult(channel="telegram", success=False, error="timeout")


class FeishuPublisher(BasePublisher):
    """飞书渠道发布器。

    通过飞书 Webhook 发送卡片消息（interactive 类型）。
    环境变量:
        FEISHU_WEBHOOK_URL: 飞书 Webhook 地址。
    """

    _TIMEOUT_SECONDS = 30.0

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or os.getenv("FEISHU_WEBHOOK_URL", "")
        if not self.webhook_url:
            logger.warning("FeishuPublisher: FEISHU_WEBHOOK_URL 未设置")

    async def send_message(self, content: str, **kwargs: Any) -> PublishResult:
        """通过飞书 Webhook 发送卡片消息。

        Args:
            content: 此处为已组装好的 card dict（而非字符串）。
            **kwargs: 支持 msg_type="interactive"（默认）。

        Returns:
            PublishResult。
        """
        msg_type = kwargs.get("msg_type", "interactive")
        if isinstance(content, dict):
            payload: dict[str, Any] = {"msg_type": msg_type, content.get("msg_type", msg_type): content}
        else:
            payload = {"msg_type": msg_type, msg_type: content}
        return await self._post(payload)

    async def send_digest(self, content: str, **kwargs: Any) -> PublishResult:
        """通过飞书 Webhook 发送多卡片日报。

        Args:
            content: 已组装好的 multiplecards 格式 content dict。
            **kwargs: 支持 extra_field 字段。

        Returns:
            PublishResult。
        """
        msg_type = kwargs.get("msg_type", "interactive")
        if isinstance(content, dict):
            payload = {"msg_type": msg_type, msg_type: content}
        else:
            payload = {"msg_type": msg_type, msg_type: content}
        return await self._post(payload)

    async def _post(self, payload: dict[str, Any]) -> PublishResult:
        """向飞书 Webhook 发送 POST 请求。

        Args:
            payload: 请求体字典。

        Returns:
            PublishResult。
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._TIMEOUT_SECONDS),
                ) as response:
                    data = await response.json()
                    if response.status == 200 and data.get("code") == 0:
                        logger.info("飞书消息发送成功")
                        return PublishResult(channel="feishu", success=True)
                    error_msg = data.get("msg", f"HTTP {response.status}")
                    logger.warning("飞书消息发送失败: %s", error_msg)
                    return PublishResult(channel="feishu", success=False, error=error_msg)
        except aiohttp.ClientError as e:
            logger.error("飞书请求异常: %s", e)
            return PublishResult(channel="feishu", success=False, error=str(e))
        except TimeoutError as e:
            logger.error("飞书请求超时: %s", e)
            return PublishResult(channel="feishu", success=False, error="timeout")


class WechatClawBotPublisher(BasePublisher):
    """微信/企业微信 ClawBot 渠道发布器。

    通过 Webhook 发送简明文本消息。
    环境变量:
        CLAWBOT_WEBHOOK_URL: ClawBot Webhook 地址。
    """

    _TIMEOUT_SECONDS = 30.0

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or os.getenv("CLAWBOT_WEBHOOK_URL", "")
        if not self.webhook_url:
            logger.warning("WechatClawBotPublisher: CLAWBOT_WEBHOOK_URL 未设置")

    async def send_message(self, content: str, **kwargs: Any) -> PublishResult:
        """通过 ClawBot Webhook 发送文本消息。

        Args:
            content: 文本内容。
            **kwargs: 支持 msg_type="text"（默认）。

        Returns:
            PublishResult。
        """
        msg_type = kwargs.get("msg_type", "text")
        payload: dict[str, Any] = {"msg_type": msg_type, msg_type: {"content": content}}
        return await self._post(payload)

    async def send_digest(self, content: str, **kwargs: Any) -> PublishResult:
        """通过 ClawBot Webhook 发送知识日报。

        Args:
            content: 日报文本内容。
            **kwargs: 同 send_message。

        Returns:
            PublishResult。
        """
        return await self.send_message(content, **kwargs)

    async def _post(self, payload: dict[str, Any]) -> PublishResult:
        """向 ClawBot Webhook 发送 POST 请求。

        Args:
            payload: 请求体字典。

        Returns:
            PublishResult。
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._TIMEOUT_SECONDS),
                ) as response:
                    data = await response.json()
                    if response.status == 200 and data.get("errcode") == 0:
                        logger.info("ClawBot 消息发送成功")
                        return PublishResult(channel="clawbot", success=True)
                    error_msg = data.get("errmsg", f"HTTP {response.status}")
                    logger.warning("ClawBot 消息发送失败: %s", error_msg)
                    return PublishResult(channel="clawbot", success=False, error=error_msg)
        except aiohttp.ClientError as e:
            logger.error("ClawBot 请求异常: %s", e)
            return PublishResult(channel="clawbot", success=False, error=str(e))
        except TimeoutError as e:
            logger.error("ClawBot 请求超时: %s", e)
            return PublishResult(channel="clawbot", success=False, error="timeout")


async def publish_daily_digest(
    knowledge_dir: str = "knowledge/articles",
    date: str | None = None,
    top_n: int = 5,
    channels: list[str] | None = None,
) -> list[PublishResult]:
    """统一异步入口，并发发布知识日报到指定渠道。

    Args:
        knowledge_dir: 知识库 articles 目录路径。
        date: 日期字符串，格式 YYYY-MM-DD，默认为今天。
        top_n: 返回条目的最大数量。
        channels: 目标渠道列表，如 ["telegram"] 或 ["feishu", "clawbot"]。
                  默认为 ["telegram", "feishu", "clawbot"]（所有渠道）。

    Returns:
        所有渠道的 PublishResult 列表。
    """
    from distribution.formatter import generate_daily_digest

    digest = generate_daily_digest(knowledge_dir=knowledge_dir, date=date, top_n=top_n)

    publishers: dict[str, BasePublisher] = {}
    if not channels or "telegram" in channels:
        publishers["telegram"] = TelegramPublisher()
    if not channels or "feishu" in channels:
        publishers["feishu"] = FeishuPublisher()
    if not channels or "clawbot" in channels:
        publishers["clawbot"] = WechatClawBotPublisher()

    results: list[PublishResult] = []

    async with aiohttp.ClientSession():
        tasks = []
        channel_names = []
        for ch, pub in publishers.items():
            tasks.append(pub.send_digest(digest[ch]))
            channel_names.append(ch)

        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        for result, ch in zip(gathered, channel_names):
            if isinstance(result, Exception):
                logger.error("发布任务异常: %s", result)
                results.append(
                    PublishResult(channel=ch, success=False, error=str(result))
                )
            else:
                results.append(result)

    return results
