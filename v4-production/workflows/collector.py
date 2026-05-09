"""Collector 节点 - GitHub 数据采集。

从 GitHub Search API 采集 AI/LLM/Agent 相关仓库，
保存原始数据到 knowledge/raw/ 目录。
"""

import json
import logging
import os
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from tests.security import sanitize_input

from .model_client import accumulate_usage
from .state import KBState

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
RAW_DIR = KNOWLEDGE_DIR / "raw"

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

SYSTEM_COLLECT = "你是一个专业的 GitHub 数据采集助手。"

AI_KEYWORDS = [
    "AI", "LLM", "agent", "artificial intelligence", "machine learning",
    "deep learning", "neural network", "RAG", "embedding", "vector database",
    "LangChain", "LangGraph", "AutoGPT", "autonomous agent",
]

STAR_THRESHOLD = 100


def _build_github_headers() -> dict[str, str]:
    """构建 GitHub API 请求头。"""
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Knowledge-Base-Bot/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _search_github_repos(query: str, sort: str = "stars", order: str = "desc",
                         per_page: int = 30) -> list[dict]:
    """搜索 GitHub 仓库。"""
    params = {
        "q": query + " in:name,description,readme",
        "sort": sort,
        "order": order,
        "per_page": str(per_page),
    }
    url = f"{GITHUB_SEARCH_URL}?{urllib.parse.urlencode(params)}"
    headers = _build_github_headers()

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    items = data.get("items", [])
    results = []
    for item in items:
        results.append({
            "url": item.get("html_url", ""),
            "title": item.get("full_name", ""),
            "description": item.get("description", "") or "",
            "stars": item.get("stargazers_count", 0),
            "language": item.get("language", ""),
            "updated_at": item.get("updated_at", ""),
        })
    return results


def _filter_ai_repos(repos: list[dict]) -> list[dict]:
    """过滤 AI/LLM/Agent 相关仓库。"""
    filtered = []
    for repo in repos:
        text = " ".join([
            repo.get("title", ""),
            repo.get("description", ""),
        ]).lower()
        if any(kw.lower() in text for kw in AI_KEYWORDS):
            filtered.append(repo)
    return filtered


def collect_node(state: KBState) -> dict:
    """采集节点：调用 GitHub Search API 获取 AI 相关仓库。

    Args:
        state: KBState

    Returns:
        dict: sources, cost_tracker
    """
    plan = state.get("plan", {}) or {}
    per_source_limit = int(plan.get("per_source_limit", 10))

    logger.info("[Collector] 开始采集 GitHub Trending 仓库（per_source_limit=%d）...", per_source_limit)

    query = " OR ".join(AI_KEYWORDS[:6])
    repos = _search_github_repos(query, per_page=per_source_limit)
    repos = [r for r in repos if r["stars"] >= STAR_THRESHOLD]
    repos = _filter_ai_repos(repos)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw_entry = {
        "date": today,
        "repos": repos,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }

    raw_file = RAW_DIR / f"{today}.json"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(raw_entry, f, ensure_ascii=False, indent=2)

    sources = [{
        "url": r["url"],
        "title": r["title"],
        "description": r["description"],
        "stars": r["stars"],
        "language": r["language"],
    } for r in repos]

    cleaned_sources = []
    suspicious_count = 0
    for src in sources:
        cleaned_title, title_warnings = sanitize_input(src.get("title", ""))
        cleaned_desc, desc_warnings = sanitize_input(src.get("description", ""))
        if title_warnings or desc_warnings:
            suspicious_count += 1
        cleaned_sources.append({
            **src,
            "title": cleaned_title,
            "description": cleaned_desc,
        })

    if suspicious_count > 0:
        logger.warning("[Collector] 清洗后发现 %d 条可疑输入已拦截", suspicious_count)

    logger.info("[Collector] 采集完成，共 %d 条符合条件的仓库", len(cleaned_sources))
    return {
        "sources": cleaned_sources,
        "cost_tracker": {"prompt_tokens": 0, "completion_tokens": 0, "total_cost_yuan": 0.0},
    }