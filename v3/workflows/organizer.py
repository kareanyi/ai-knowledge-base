"""Organizer 节点 - 整理与保存。

过滤低分条目、按 URL 去重、写入文件、更新索引。
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .model_client import chat_json, accumulate_usage
from .state import KBState

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
ARTICLES_DIR = KNOWLEDGE_DIR / "articles"
INDEX_FILE = ARTICLES_DIR / "index.json"

SYSTEM_ORGANIZE = "你是一个知识库组织专家，负责过滤、去重和修正条目。"


def _dedup_by_url(items: list[dict]) -> list[dict]:
    """按 URL 去重，保留分数最高的。"""
    seen: dict[str, dict] = {}
    for item in items:
        url = item.get("url") or item.get("source_url", "")
        score = item.get("relevance_score", 0.0)
        if url not in seen or score > seen[url].get("relevance_score", 0.0):
            seen[url] = item
    return list(seen.values())


def _apply_feedback_correction(items: list[dict], feedback: str) -> list[dict]:
    """如果有审核反馈，调用 LLM 做定向修正。"""
    if not feedback:
        return items

    prompt = (
        "你是一个知识库组织专家。收到一批条目及其审核反馈，请对条目进行修正。\n\n"
        f"审核反馈:\n{feedback}\n\n"
        "条目列表（JSON 数组）:\n" + json.dumps(items, ensure_ascii=False, indent=2) + "\n\n"
        "请返回修正后的 JSON 数组，保持相同结构，只修正有问题的部分。"
    )

    try:
        corrected, usage = chat_json(prompt, system=SYSTEM_ORGANIZE)
    except Exception as e:
        logger.warning("[Organizer] 审核反馈修正 LLM 调用失败: %s，跳过修正", e)
        return items
    if isinstance(corrected, list):
        return corrected
    return items


def _update_index(articles: list[dict]) -> None:
    """更新 index.json 索引文件。"""
    index_data = []
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            index_data = []

    existing_ids = {item["id"] for item in index_data}
    for article in articles:
        article_id = article.get("id", "")
        if article_id and article_id not in existing_ids:
            index_data.append({
                "id": article_id,
                "title": article.get("title", ""),
                "category": article.get("category", ""),
                "relevance_score": article.get("relevance_score", 0.0),
            })
            existing_ids.add(article_id)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)


def organize_node(state: KBState) -> dict:
    """整理+保存节点：过滤、去重、赋值 ID、写入文件、更新索引。

    在 review 通过后执行，负责将 analyses 转化为最终可发布的知识条目。

    Args:
        state: KBState，包含 analyses, iteration, review_feedback

    Returns:
        dict: saved_ids
    """
    analyses = state.get("analyses", [])
    iteration = state.get("iteration", 0)
    feedback = state.get("review_feedback", "")

    plan = state.get("plan", {}) or {}
    relevance_threshold = float(plan.get("relevance_threshold", 0.5))

    logger.info("[Organizer] 开始整理并保存 %d 条 analyses...", len(analyses))

    articles = [a for a in analyses if a.get("relevance_score", 0) >= relevance_threshold]
    logger.info("[Organizer] 过滤后（score>=%.1f）：%d 条", relevance_threshold, len(articles))

    before_dedup = len(articles)
    articles = _dedup_by_url(articles)
    logger.info("[Organizer] 去重后：%d 条（移除 %d 条重复）", len(articles), before_dedup - len(articles))

    if iteration > 0 and feedback:
        logger.info("[Organizer] 应用审核反馈修正...")
        articles = _apply_feedback_correction(articles, feedback)

    for idx, article in enumerate(articles):
        if "id" not in article:
            article["id"] = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{idx:03d}"
        if "source" not in article:
            article["source"] = "github"
        if "collected_at" not in article:
            article["collected_at"] = datetime.now(timezone.utc).isoformat()

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    saved_ids = []

    for idx, article in enumerate(articles):
        article_id = article.get("id")
        if not article_id:
            continue

        file_path = ARTICLES_DIR / f"{article_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(article, f, ensure_ascii=False, indent=2)

        saved_ids.append(article_id)
        logger.info("[Organizer] 保存进度 %d/%d（iteration=%d）: %s", idx + 1, len(articles), iteration, article_id)

    _update_index(articles)

    logger.info("[Organizer] 整理保存完成，共 %d 条，已更新索引", len(saved_ids))
    return {"saved_ids": saved_ids}