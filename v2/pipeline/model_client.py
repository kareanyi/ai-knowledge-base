"""统一的 LLM 调用客户端。

支持 DeepSeek、Qwen、Minimax 三种模型提供商，
通过环境变量切换，默认 minimax。
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar
from collections import defaultdict

import httpx

logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "minimax").lower()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_API_KEY_V2 = os.getenv("MINIMAX_API_KEY_V2", "")


@dataclass
class LLMResponse:
    """LLM 调用的统一响应结构。"""

    content: str
    usage: dict[str, int] = field(default_factory=dict)
    raw_response: dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """追踪 LLM 调用的 token 消耗和成本。

    Attributes:
        PRICING: 国产模型价格表，单位：元/百万 tokens。
    """

    PRICING: ClassVar[dict[str, tuple[float, float]]] = {
        "deepseek": (1.0, 2.0),
        "qwen": (4.0, 12.0),
        "minimax": (2.1, 8.4),
        "minimax2.7": (2.1, 8.4),
    }

    def __init__(self) -> None:
        self._input_tokens: defaultdict[str, int] = defaultdict(int)
        self._output_tokens: defaultdict[str, int] = defaultdict(int)
        self._call_counts: defaultdict[str, int] = defaultdict(int)

    def record(self, usage: dict[str, int], provider: str) -> None:
        """记录一次 API 调用。

        Args:
            usage: token 使用量，包含 prompt_tokens/completion_tokens 或 input_tokens/output_tokens。
            provider: 提供商名称。
        """
        name = provider.lower().replace("provider", "").strip()
        self._input_tokens[name] += usage.get("prompt_tokens", usage.get("input_tokens", 0))
        self._output_tokens[name] += usage.get("completion_tokens", usage.get("output_tokens", 0))
        self._call_counts[name] += 1

    def estimated_cost(self, provider: str | None = None) -> float:
        """返回估算成本（元）。

        Args:
            provider: 提供商名称，为 None 则汇总所有提供商。

        Returns:
            估算成本（元）。
        """
        def normalize(name: str) -> str:
            return name.lower().replace("provider", "").strip()

        if provider:
            name = normalize(provider)
            input_price, output_price = self.PRICING.get(name, (2.1, 8.4))
            input_tokens = self._input_tokens[name]
            output_tokens = self._output_tokens[name]
            return (input_tokens * input_price + output_tokens * output_price) / 1_000_000

        total = 0.0
        for name in self._input_tokens:
            input_price, output_price = self.PRICING.get(name, (2.1, 8.4))
            total += (self._input_tokens[name] * input_price + self._output_tokens[name] * output_price) / 1_000_000
        return total

    def report(self, provider: str | None = None) -> None:
        """打印成本报告。

        Args:
            provider: 提供商名称，为 None 则打印所有提供商的汇总报告。
        """
        def normalize(name: str) -> str:
            return name.lower().replace("provider", "").strip()

        if provider:
            name = normalize(provider)
            input_t = self._input_tokens.get(name, 0)
            output_t = self._output_tokens.get(name, 0)
            cost = self.estimated_cost(name)
            logger.info(
                "[CostTracker] %s - calls: %d, input: %d tokens, output: %d tokens, cost: ¥%.4f",
                name,
                self._call_counts.get(name, 0),
                input_t,
                output_t,
                cost,
            )
        else:
            for name in self._input_tokens:
                input_t = self._input_tokens[name]
                output_t = self._output_tokens[name]
                cost = self.estimated_cost(name)
                logger.info(
                    "[CostTracker] %s - calls: %d, input: %d tokens, output: %d tokens, cost: ¥%.4f",
                    name,
                    self._call_counts.get(name, 0),
                    input_t,
                    output_t,
                    cost,
                )
            total_cost = self.estimated_cost()
            total_calls = sum(self._call_counts.values())
            logger.info("[CostTracker] TOTAL - calls: %d, cost: ¥%.4f", total_calls, total_cost)


tracker = CostTracker()


class LLMProvider(ABC):
    """LLM 提供商的抽象基类。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称。"""

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        """发送对话请求。

        Args:
            messages: 对话消息列表，格式为 [{"role": "user", "content": "..."}]。
            **kwargs: 传递给模型的额外参数。

        Returns:
            LLMResponse 对象。
        """

    @abstractmethod
    def get_base_url(self) -> str:
        """获取 API 基础 URL。"""

    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称。"""

    def get_headers(self) -> dict[str, str]:
        """获取请求头。"""
        return {"Content-Type": "application/json"}


class OpenAICompatibleProvider(LLMProvider):
    """兼容 OpenAI API 格式的 LLM 提供商。"""

    BASE_URL: ClassVar[str] = ""
    MODEL_NAME: ClassVar[str] = ""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def get_base_url(self) -> str:
        return self.BASE_URL

    def get_model_name(self) -> str:
        return self.MODEL_NAME

    def get_headers(self) -> dict[str, str]:
        headers = super().get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        url = f"{self.get_base_url().rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.get_model_name(),
            "messages": messages,
            **kwargs,
        }
        response = _request_with_retry("POST", url, headers=self.get_headers(), json=payload)
        data = response.json()

        choices = data.get("choices", [])
        content = ""
        if choices and len(choices) > 0:
            content = choices[0].get("message", {}).get("content", "")

        usage = data.get("usage", {})
        if usage:
            tracker.record(usage, self.name)

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response=data,
        )


class AnthropicCompatibleProvider(LLMProvider):
    """兼容 Anthropic API 格式的 LLM 提供商。"""

    BASE_URL: ClassVar[str] = ""
    MODEL_NAME: ClassVar[str] = ""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def get_base_url(self) -> str:
        return self.BASE_URL

    def get_model_name(self) -> str:
        return self.MODEL_NAME

    def get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "x-api-key": self.api_key}
        if "anthropic" in self.BASE_URL.lower():
            headers["anthropic-version"] = "2023-06-01"
        return headers

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        url = f"{self.get_base_url().rstrip('/')}/messages"
        system_message = ""
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content", "")
            else:
                filtered_messages.append(msg)

        payload: dict[str, Any] = {
            "model": self.get_model_name(),
            "messages": filtered_messages,
            **kwargs,
        }
        if system_message:
            payload["system"] = system_message

        response = _request_with_retry("POST", url, headers=self.get_headers(), json=payload)
        data = response.json()

        content = ""
        if "content" in data:
            for block in data["content"]:
                if block.get("type") == "text":
                    content += block.get("text", "")

        usage = {
            "input_tokens": data.get("usage", {}).get("input_tokens", 0),
            "output_tokens": data.get("usage", {}).get("output_tokens", 0),
        }
        if usage.get("input_tokens") or usage.get("output_tokens"):
            tracker.record(usage, self.name)

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response=data,
        )


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek 模型提供商。"""

    BASE_URL = "https://api.deepseek.com"
    MODEL_NAME = "deepseek-chat"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key or DEEPSEEK_API_KEY)


class QwenProvider(OpenAICompatibleProvider):
    """Qwen 模型提供商。"""

    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL_NAME = "qwen-plus"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key or QWEN_API_KEY)


class MinimaxProvider(OpenAICompatibleProvider):
    """Minimax 模型提供商。"""

    BASE_URL = "https://api.minimax.chat/v1"
    MODEL_NAME = "MiniMax-M2.7"

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or MINIMAX_API_KEY_V2 or MINIMAX_API_KEY
        super().__init__(key)


PROVIDER_MAP: dict[str, type[LLMProvider]] = {
    "deepseek": DeepSeekProvider,
    "qwen": QwenProvider,
    "minimax": MinimaxProvider,
}


def get_provider(provider: str | None = None) -> LLMProvider:
    """获取 LLM 提供商实例。

    Args:
        provider: 提供商名称，不填则使用 LLM_PROVIDER 环境变量。

    Returns:
        LLMProvider 实例。

    Raises:
        ValueError: 不支持的提供商。
    """
    name = (provider or LLM_PROVIDER).lower()
    if name not in PROVIDER_MAP:
        raise ValueError(f"Unsupported provider: {name}. Supported: {list(PROVIDER_MAP.keys())}")
    return PROVIDER_MAP[name]()


def _request_with_retry(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    json: dict[str, Any] | None = None,
    timeout: float = 60.0,
    max_retries: int = 3,
) -> httpx.Response:
    """发送 HTTP 请求，带指数退避重试。

    Args:
        method: HTTP 方法。
        url: 请求 URL。
        headers: 请求头。
        json: JSON 请求体。
        timeout: 超时秒数。
        max_retries: 最大重试次数。

    Returns:
        httpx.Response 对象。
    """
    retry_count = 0
    backoff = 1.0
    while True:
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.request(method, url, headers=headers, json=json)
                response.raise_for_status()
                return response
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if retry_count >= max_retries:
                logger.error("Request failed after %d retries: %s", max_retries, e)
                raise
            logger.warning(
                "Request failed (attempt %d/%d): %s. Retrying in %.1fs...",
                retry_count + 1,
                max_retries,
                e,
                backoff,
            )
            time.sleep(backoff)
            retry_count += 1
            backoff *= 2


def chat_with_retry(
    messages: list[dict[str, str]],
    provider: str | None = None,
    **kwargs: Any,
) -> LLMResponse:
    """发送对话请求，带重试机制。

    Args:
        messages: 对话消息列表。
        provider: 提供商名称。
        **kwargs: 传递给模型的额外参数。

    Returns:
        LLMResponse 对象。
    """
    p = get_provider(provider)
    return p.chat(messages, **kwargs)


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量（粗略估算）。

    按照中文约 2 字符/token，英文约 4 字符/token 计算。

    Args:
        text: 输入文本。

    Returns:
        估算的 token 数量。
    """
    chinese_chars = sum(1 for c in text if ord(c) > 127)
    other_chars = len(text) - chinese_chars
    return chinese_chars // 2 + other_chars // 4


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    provider: str | None = None,
) -> float:
    """计算 LLM 调用的美元成本。

    Args:
        input_tokens: 输入 token 数量。
        output_tokens: 输出 token 数量。
        provider: 提供商名称。

    Returns:
        成本（USD）。
    """
    name = (provider or LLM_PROVIDER).lower()

    pricing: dict[str, tuple[float, float]] = {
        "deepseek": (0.000001, 0.000002),
        "qwen": (0.0000015, 0.000006),
        "minimax": (0.000001, 0.000005),
    }

    if name not in pricing:
        logger.warning("Unknown provider %s, using minimax pricing", name)
        name = "minimax"

    input_price, output_price = pricing[name]
    return input_tokens * input_price + output_tokens * output_price


def quick_chat(
    prompt: str,
    system: str = "",
    provider: str | None = None,
    **kwargs: Any,
) -> str:
    """便捷的 LLM 调用函数，一句话完成对话。

    Args:
        prompt: 用户 prompt。
        system: 系统消息，可选。
        provider: 提供商名称。
        **kwargs: 传递给模型的额外参数。

    Returns:
        LLM 返回的内容。
    """
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = chat_with_retry(messages, provider, **kwargs)

    input_tokens = response.usage.get("prompt_tokens", estimate_tokens(prompt))
    output_tokens = response.usage.get("completion_tokens", estimate_tokens(response.content))
    cost = calculate_cost(input_tokens, output_tokens, provider)

    logger.info(
        "[%s] prompt_tokens=%d completion_tokens=%d cost=%.6f USD",
        provider or LLM_PROVIDER,
        input_tokens,
        output_tokens,
        cost,
    )

    return response.content


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    test_prompt = "用一句话解释量子计算"

    print(f"Testing with prompt: {test_prompt}")
    print("-" * 50)

    result = quick_chat(test_prompt)
    print(f"Response: {result}")
