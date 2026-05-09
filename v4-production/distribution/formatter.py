"""Formatter 模块 - 多渠道分发格式转换。

提供 JSON 条目到各平台格式的转换能力，支持：
- Markdown（通用格式）
- Telegram MarkdownV2
- 飞书 interactive 卡片
- 微信/企业微信/CrabBot 简明文本
- 日报聚合
"""

import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

SCORE_EMOJI = {
    "green": "🟢",
    "yellow": "🟡",
    "red": "🔴",
}

TELEGRAM_ESCAPE_PATTERN = re.compile(r"([_*\[\]()~`>#+\-=|{}.!])")
FEISHU_HEADER_COLOR = {
    "green": "#00A381",
    "yellow": "#FFB200",
    "red": "#D71D30",
}


def _score_to_indicator(score: float) -> str:
    """根据分数返回 emoji 指示器。"""
    if score >= 0.8:
        return SCORE_EMOJI["green"]
    if score >= 0.6:
        return SCORE_EMOJI["yellow"]
    return SCORE_EMOJI["red"]


def _score_to_feishu_color(score: float) -> str:
    """根据分数返回飞书 header 颜色。"""
    if score >= 0.8:
        return "green"
    if score >= 0.6:
        return "yellow"
    return "red"


def _escape_telegram(text: str) -> str:
    """转义 Telegram MarkdownV2 特殊字符。"""
    return TELEGRAM_ESCAPE_PATTERN.sub(r"\\\1", text)


def json_to_markdown(article: dict) -> str:
    """将单篇文章 JSON 转换为 Markdown 格式。

    Args:
        article: 单篇文章字典，需包含 id, title, source, collected_at,
            relevance_score, tags, summary, url 字段。

    Returns:
        Markdown 格式字符串。
    """
    title = article.get("title", "Untitled")
    source = article.get("source", "unknown")
    collected_at = article.get("collected_at", "")[:10]
    score = float(article.get("relevance_score", 0.0))
    tags = article.get("tags", [])
    summary = article.get("summary", "")
    url = article.get("url", article.get("source_url", ""))

    indicator = _score_to_indicator(score)
    tags_str = " / ".join(tags) if tags else "无"

    return (
        f"## {title}\n\n"
        f"**来源**: {source} | **日期**: {collected_at} | "
        f"**相关性**: {indicator} {score:.1f}\n\n"
        f"**标签**: {tags_str}\n\n"
        f"{summary}\n\n"
        f"🔗 原文: {url}"
    )


def json_to_telegram(article: dict) -> str:
    """将单篇文章 JSON 转换为 Telegram MarkdownV2 格式。

    Args:
        article: 单篇文章字典。

    Returns:
        Telegram MarkdownV2 格式字符串。
    """
    title = _escape_telegram(article.get("title", "Untitled"))
    source = _escape_telegram(article.get("source", "unknown"))
    score = float(article.get("relevance_score", 0.0))
    tags = article.get("tags", [])
    summary = _escape_telegram(article.get("summary", ""))
    url = article.get("url", article.get("source_url", ""))

    indicator = _score_to_indicator(score)
    tags_str = " ".join(t.replace(" ", "_") for t in tags) if tags else "无"

    return (
        f"*{title}*\n"
        f"📊 {indicator} {score:.1f} | 📂 {source}\n"
        f"🏷️ {tags_str}\n\n"
        f"{summary}\n\n"
        f"🔗 {url}"
    )


def json_to_feishu(article: dict) -> dict:
    """将单篇文章 JSON 转换为飞书 interactive 卡片格式。

    Args:
        article: 单篇文章字典。

    Returns:
        飞书 interactive 卡片 dict，包含 msg_type 和 card 配置。
    """
    title = article.get("title", "Untitled")
    source = article.get("source", "unknown")
    score = float(article.get("relevance_score", 0.0))
    tags = article.get("tags", [])
    summary = article.get("summary", "")
    url = article.get("url", article.get("source_url", ""))

    color_key = _score_to_feishu_color(score)
    header_color = FEISHU_HEADER_COLOR[color_key]
    tags_str = " ".join(tags) if tags else "无"

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": header_color,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**来源**: {source}  |  **相关性**: {score:.1f}\n"
                            f"**标签**: {tags_str}"
                        ),
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": summary},
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "a",
                            "text": {"tag": "plain_text", "content": "🔗 查看原文"},
                            "href": url,
                        }
                    ],
                },
            ],
        },
    }


def json_to_wechat_clawbot(article: dict) -> str:
    """将单篇文章 JSON 转换为简明文本（适用于微信/企业微信/CrabBot 等）。

    Args:
        article: 单篇文章字典。

    Returns:
        简明文本字符串，包含标题、评分、标签和链接。
    """
    title = article.get("title", "Untitled")
    score = float(article.get("relevance_score", 0.0))
    tags = article.get("tags", [])
    summary = article.get("summary", "")
    url = article.get("url", article.get("source_url", ""))

    indicator = _score_to_indicator(score)
    tags_str = " ".join(tags) if tags else ""

    lines = [f"{indicator} {title} ({score:.1f})"]
    if tags_str:
        lines.append(f"[{tags_str}]")
    if summary:
        lines.append(summary[:100] + ("..." if len(summary) > 100 else ""))
    lines.append(url)

    return " | ".join(lines)


def generate_daily_digest(
    knowledge_dir: str = "knowledge/articles",
    date: Optional[str] = None,
    top_n: int = 5,
) -> dict:
    """生成当日知识简报，支持多渠道分发格式。

    Args:
        knowledge_dir: 知识库 articles 目录路径。
        date: 日期字符串，格式 YYYY-MM-DD，默认为今天。
        top_n: 返回条目的最大数量，按 relevance_score 降序排列。

    Returns:
        dict: 包含 markdown、telegram、feishu 三种格式字符串的字典。
        feishu 为 list[dict]（飞书 multiplecards 格式），当日无文章时
        返回 {"markdown": "📭 ...", "telegram": "📭 ...", "feishu": []}。
    """
    if date is None:
        date = datetime.now().date().isoformat()

    pattern = f"{date}-*.json"
    article_files = sorted(Path(knowledge_dir).glob(pattern), reverse=True)

    if not article_files:
        msg = f"📭 {date} 暂无新增知识条目"
        return {"markdown": msg, "telegram": msg, "feishu": []}

    articles: list[dict] = []
    for fp in article_files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                articles.append(__import__("json").load(f))
        except Exception:
            continue

    articles.sort(key=lambda a: a.get("relevance_score", 0.0), reverse=True)
    top_articles = articles[:top_n]

    md_parts = [f"# 📚 {date} 知识简报（共 {len(top_articles)} 条）\n"]
    tg_parts = [f"📚 *{date} 知识简报*（共 {len(top_articles)} 条）\n"]
    feishu_cards: list[dict] = []

    for article in top_articles:
        md_parts.append(json_to_markdown(article))
        md_parts.append("\n---\n")

        tg_parts.append(json_to_telegram(article))
        tg_parts.append("\n" + "─" * 20 + "\n")

        feishu_cards.append(json_to_feishu(article))

    return {
        "markdown": "".join(md_parts).strip(),
        "telegram": "".join(tg_parts).strip(),
        "feishu": feishu_cards,
    }


def generate_daily_digest_clawbot(
    knowledge_dir: str = "knowledge/articles",
    date: Optional[str] = None,
    top_n: int = 5,
) -> dict:
    """生成当日知识简报（ClawBot 格式）。

    Args:
        knowledge_dir: 知识库 articles 目录路径。
        date: 日期字符串，格式 YYYY-MM-DD，默认为今天。
        top_n: 返回条目的最大数量，按 relevance_score 降序排列。

    Returns:
        dict: 包含 clawbot 格式字符串的字典，当日无文章时
        返回 {"clawbot": "📭 ..."}。
    """
    if date is None:
        date = datetime.now().date().isoformat()

    pattern = f"{date}-*.json"
    article_files = sorted(Path(knowledge_dir).glob(pattern), reverse=True)

    if not article_files:
        msg = f"📭 {date} 暂无新增知识条目"
        return {"clawbot": msg}

    articles: list[dict] = []
    for fp in article_files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                articles.append(__import__("json").load(f))
        except Exception:
            continue

    articles.sort(key=lambda a: a.get("relevance_score", 0.0), reverse=True)
    top_articles = articles[:top_n]

    lines = [f"📚 {date} 知识简报（共 {len(top_articles)} 条）\n"]
    for i, article in enumerate(top_articles, 1):
        lines.append(f"{i}. {json_to_wechat_clawbot(article)}")
        lines.append("")

    return {"clawbot": "\n".join(lines).strip()}
