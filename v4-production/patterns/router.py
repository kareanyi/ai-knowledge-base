"""Router 路由模式：两层意图分类 + 三种处理器。

两层意图分类：
- 第一层：关键词快速匹配（零成本，不调 LLM）
- 第二层：LLM 分类兜底（处理模糊意图）

三种意图：github_search / knowledge_query / general_chat
"""

import json
import logging
import os
import re
from urllib.parse import quote
from urllib.request import urlopen, Request
from typing import Literal


from workflows.model_client import chat, chat_json

logger = logging.getLogger(__name__)

IndexEntry = dict[str, str | float]

GITHUB_KEYWORDS = {
    "github", "repo", "repository", "stars", "forks", "open source",
    "search", "搜索", "github 项目", "github search",
    "仓库", "项目", "git"
}
KNOWLEDGE_KEYWORDS = {
    "知识库", "article", "knowledge", "rag", "dify", "langchain",
    "browser-use", "hermes-agent", "ragflow", "openhands", "llamafactory",
    "deer-flow", "mem0", "awesome-llm-apps", "infiniflow",
    "什么是", "介绍", "解释", "是什么"
}

Intent = Literal["github_search", "knowledge_query", "general_chat"]


def _classify_by_keywords(query: str) -> Intent | None:
    """第一层：关键词快速匹配。

    Args:
        query: 用户输入。

    Returns:
        匹配的意图类型，或 None（需 LLM 兜底）。
    """
    q = query.lower()
    github_score = sum(1 for kw in GITHUB_KEYWORDS if kw in q)
    knowledge_score = sum(1 for kw in KNOWLEDGE_KEYWORDS if kw in q)

    if github_score >= 1 and knowledge_score == 0:
        return "github_search"
    if knowledge_score >= 1:
        return "knowledge_query"
    if github_score == 1 and knowledge_score == 1:
        return "github_search" if "github" in q else "knowledge_query"

    return None


def _classify_by_llm(query: str) -> Intent:
    """第二层：LLM 分类兜底。

    Args:
        query: 用户输入。

    Returns:
        意图类型。
    """
    system = "你是一个意图分类器。分析用户问题，从以下三类中选择最合适的意图并只返回意图名称：\n- github_search：用户想搜索 GitHub 项目或查询仓库信息\n- knowledge_query：用户想查询知识库中的 AI/LLM/Agent 相关内容，或询问某个项目的介绍/解释\n- general_chat：用户的闲聊、问候或不属于前两类的问题\n\n只返回一个词：github_search 或 knowledge_query 或 general_chat"
    prompt = f"用户问题：{query}\n意图："
    intent_text, _ = chat(prompt, system=system, temperature=0)
    intent = intent_text.strip().lower()

    if "github_search" in intent:
        return "github_search"
    if "knowledge_query" in intent:
        return "knowledge_query"
    return "general_chat"


def classify_intent(query: str) -> Intent:
    """两层意图分类。

    Args:
        query: 用户输入。

    Returns:
        匹配的意图类型。
    """
    intent = _classify_by_keywords(query)
    if intent:
        logger.info("Intent classified by keywords: %s", intent)
        return intent

    logger.info("Intent fallback to LLM classification")
    return _classify_by_llm(query)


def _search_github_api(query: str) -> str:
    """调用 GitHub Search API 搜索仓库。

    Args:
        query: 搜索关键词。

    Returns:
        格式化的搜索结果文本。
    """
    token = os.getenv("GITHUB_TOKEN", "")
    encoded_q = quote(query)
    url = f"https://api.github.com/search/repositories?q={encoded_q}&per_page=5&sort=stars&order=desc"
    headers: dict[str, str] = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ai-knowledge-base-router",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        items = data.get("items", [])
        if not items:
            return "未找到相关仓库。"

        lines = [f"GitHub 搜索「{query}」结果："]
        for i, item in enumerate(items, 1):
            lines.append(
                f"\n{i}. {item['full_name']} ⭐ {item['stargazers_count']:,} "
                f"| Fork {item['forks_count']:,}\n"
                f"   描述：{item.get('description') or '无描述'}\n"
                f"   链接：{item['html_url']}"
            )
        return "\n".join(lines)

    except Exception as e:
        logger.error("GitHub search failed: %s", e)
        return f"GitHub 搜索失败：{e}"


def _search_knowledge(query: str) -> str:
    """从本地知识库检索相关条目。

    Args:
        query: 搜索关键词。

    Returns:
        检索结果文本。
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_path = os.path.join(base_dir, "knowledge", "articles", "index.json")

    try:
        with open(index_path, encoding="utf-8") as f:
            index: list[IndexEntry] = json.load(f)
    except Exception as e:
        logger.error("Failed to load index: %s", e)
        return f"加载知识库索引失败：{e}"

    q = query.lower()
    scored: list[tuple[float, str]] = []
    for entry in index:
        title = entry.get("title", "").lower()
        category = entry.get("category", "").lower()
        score = 0.0
        for kw in q.split():
            if kw in title:
                score += 0.5
            if kw in category:
                score += 0.3
        if score > 0:
            scored.append((score, entry["id"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_ids = [item[1] for item in scored[:3]]

    if not top_ids:
        return "知识库中未找到相关内容。"

    results: list[str] = [f"知识库检索「{query}」相关条目："]
    for rid in top_ids:
        article_path = os.path.join(base_dir, "knowledge", "articles", f"{rid}.json")
        try:
            with open(article_path, encoding="utf-8") as f:
                article = json.load(f)
            results.append(
                f"\n- {article.get('title', rid)}\n"
                f"  摘要：{article.get('summary', '无')[:150]}...\n"
                f"  标签：{', '.join(article.get('tags', []))}\n"
                f"  来源：{article.get('url', '无')}"
            )
        except Exception as e:
            logger.warning("Failed to load article %s: %s", rid, e)

    return "\n".join(results)


def _general_chat(query: str) -> str:
    """通用对话：直接调用 LLM 回答。

    Args:
        query: 用户问题。

    Returns:
        LLM 回复文本。
    """
    system = "你是一个专业的 AI 技术分析师，专注于 AI/LLM/Agent 领域。请专业、简洁地回答用户问题。"
    text, usage = chat(query, system=system, temperature=0.3, max_tokens=1500)
    logger.info("general_chat usage: %s", usage)
    return text


INTENT_HANDLERS: dict[Intent, callable] = {
    "github_search": _search_github_api,
    "knowledge_query": _search_knowledge,
    "general_chat": _general_chat,
}


def route(query: str) -> str:
    """统一路由入口。

    Args:
        query: 用户输入。

    Returns:
        处理结果文本。
    """
    intent = classify_intent(query)
    logger.info("Routing to %s, query=%s", intent, query[:50])

    handler = INTENT_HANDLERS[intent]
    return handler(query)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f">>> {query}")
        print("-" * 40)
        print(route(query))
    else:
        test_queries = [
            "search github for langchain related projects",
            "介绍 dify 这个项目",
            "你好，今天天气怎么样？",
            "帮我查一下 awesome-llm-apps 是什么",
            "github 搜索 openai agent",
        ]
        print("Router 测试\n" + "=" * 60)
        for q in test_queries:
            print(f"\n>>> {q}")
            print("-" * 40)
            result = route(q)
            print(result[:300])
