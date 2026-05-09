"""LangGraph 工作流节点定义。

定义 5 个纯函数节点：collect, analyze, organize, review, save。
各节点接收 KBState，返回 dict（部分状态更新）。
"""

import json
import logging
import os
import urllib.request
import urllib.parse
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .model_client import chat, chat_json, accumulate_usage
from .state import KBState

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
ARTICLES_DIR = KNOWLEDGE_DIR / "articles"
INDEX_FILE = ARTICLES_DIR / "index.json"
RAW_DIR = KNOWLEDGE_DIR / "raw"

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

SYSTEM_COLLECT = "你是一个专业的 GitHub 数据采集助手。"
SYSTEM_ANALYZE = "你是一个专业的 AI 技术分析师，负责为每条技术条目生成结构化的中文摘要和标签。"
SYSTEM_REVIEW = "你是一个严格的质量审核员，从四个维度对知识条目进行评分。"
SYSTEM_ORGANIZE = "你是一个知识库组织专家，负责过滤、去重和修正条目。"
SYSTEM_SAVE = "你是一个文档存储专家。"

AI_KEYWORDS = ["AI", "LLM", "agent", "artificial intelligence", "machine learning",
                "deep learning", "neural network", "RAG", "embedding", "vector database",
                "LangChain", "LangGraph", "AutoGPT", "autonomous agent", "RAG"]

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
    """采集节点：调用 GitHub Search API 获取 AI 相关仓库。"""
    logger.info("[Collector] 开始采集 GitHub Trending 仓库...")

    query = " OR ".join(AI_KEYWORDS[:6])
    repos = _search_github_repos(query, per_page=50)
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

    logger.info("[Collector] 采集完成，共 %d 条符合条件的仓库", len(sources))
    return {
        "sources": sources,
        "cost_tracker": {"prompt_tokens": 0, "completion_tokens": 0, "total_cost_yuan": 0.0},
    }


def _analyze_single(item: dict, idx: int, iteration: int, feedback: str | None) -> dict:
    """对单条数据调用 LLM 生成分析结果。"""
    title = item.get("title", "")
    description = item.get("description", "")
    url = item.get("url", "")
    stars = item.get("stars", 0)

    prompt_parts = [
        f"## 待分析条目 #{idx + 1}",
        f"标题: {title}",
        f"URL: {url}",
        f"描述: {description}",
        f"Stars: {stars}",
    ]

    if iteration > 0 and feedback:
        prompt_parts.append(f"\n## 审核反馈（请据此修正）:\n{feedback}")

    prompt_parts.append("\n请为上述条目生成结构化分析结果，以 JSON 格式输出，包含以下字段：")
    prompt_parts.append('{"summary": "一句话中文摘要", "tech_stack": ["技术栈列表"], '
                       '"tags": ["中文标签列表"], "problem_solved": "解决什么问题", '
                       '"why_valuable": "为什么有价值", "category": "分类（framework/agent/tool/rag/llm）", '
                       '"relevance_score": 0.0-1.0评分"}')

    prompt = "\n".join(prompt_parts)

    system = SYSTEM_ANALYZE
    if iteration > 0 and feedback:
        system = "你是一个专业的 AI 技术分析师，负责根据审核反馈修正之前的分析结果，使其更准确、质量更高。"

    try:
        result, usage = chat_json(prompt, system=system, node_name="analyzer")
    except Exception as e:
        logger.warning("[Analyzer] 条目 #%d LLM 调用失败: %s，使用 fallback", idx + 1, e)
        result = {
            "summary": f"（LLM 解析失败）{description[:50]}..." if description else "（无描述）",
            "tech_stack": [],
            "tags": [],
            "problem_solved": "未知",
            "why_valuable": "未知",
            "category": "unknown",
            "relevance_score": 0.0,
        }
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
    return {"item": item, "analysis": result, "usage": usage}


def analyze_node(state: KBState) -> dict:
    """分析节点：用 LLM 对每条数据生成中文摘要、标签、评分。"""
    sources = state.get("sources", [])
    iteration = state.get("iteration", 0)
    feedback = state.get("review_feedback", "")

    logger.info("[Analyzer] 开始分析 %d 条数据（iteration=%d）...", len(sources), iteration)

    analyses = []
    tracker = state.get("cost_tracker", {"prompt_tokens": 0, "completion_tokens": 0, "total_cost_yuan": 0.0})

    for idx, item in enumerate(sources):
        result = _analyze_single(item, idx, iteration, feedback if idx == 0 else None)
        analyses.append(result["analysis"])
        tracker = accumulate_usage(tracker, result["usage"])
        logger.info("[Analyzer] 完成 %d/%d 条", idx + 1, len(sources))

    logger.info("[Analyzer] 分析完成，共 %d 条，cost=¥%.4f",
                 len(analyses), tracker.get("total_cost_yuan", 0))
    return {"analyses": analyses, "cost_tracker": tracker}


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
        corrected, usage = chat_json(prompt, system=SYSTEM_ORGANIZE, node_name="organizer")
    except Exception as e:
        logger.warning("[Organizer] 审核反馈修正 LLM 调用失败: %s，跳过修正", e)
        return items
    if isinstance(corrected, list):
        return corrected
    return items


def organize_node(state: KBState) -> dict:
    """组织节点：过滤低分条目、按 URL 去重、应用审核反馈修正。"""
    analyses = state.get("analyses", [])
    iteration = state.get("iteration", 0)
    feedback = state.get("review_feedback", "")

    logger.info("[Organizer] 开始组织 %d 条数据（iteration=%d）...", len(analyses), iteration)

    articles = [a for a in analyses if a.get("relevance_score", 0) >= 0.6]
    logger.info("[Organizer] 过滤后（score>=0.6）：%d 条", len(articles))

    before_dedup = len(articles)
    articles = _dedup_by_url(articles)
    logger.info("[Organizer] 去重后：%d 条（移除 %d 条重复）", len(articles), before_dedup - len(articles))

    if iteration > 0 and feedback:
        logger.info("[Organizer] 应用审核反馈修正...")
        articles = _apply_feedback_correction(articles, feedback)

    for idx, article in enumerate(articles):
        if "id" not in article:
            article["id"] = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{idx:03d}"

    logger.info("[Organizer] 组织完成，共 %d 条待审文章", len(articles))
    return {"articles": articles}


def review_node(state: KBState) -> dict:
    """审核节点：LLM 四维度评分，iteration>=2 强制通过。"""
    articles = state.get("articles", [])
    iteration = state.get("iteration", 0)

    logger.info("[Reviewer] 开始审核 %d 条数据（iteration=%d）...", len(articles), iteration)

    if iteration >= 2:
        logger.info("[Reviewer] iteration=%d，强制通过", iteration)
        return {
            "review_passed": True,
            "review_feedback": "",
            "iteration": iteration,
        }

    if not articles:
        return {"review_passed": True, "review_feedback": "", "iteration": iteration}

    prompt = (
        "你是一个严格的质量审核员，从以下四个维度对知识条目进行评分：\n"
        "1. 摘要质量（summary_quality）：摘要是否准确、简洁、有信息量\n"
        "2. 标签准确（tags_accuracy）：标签是否与内容高度相关、覆盖面合适\n"
        "3. 分类合理（category_appropriateness）：分类是否恰当反映条目本质\n"
        "4. 一致性（consistency）：各字段是否相互一致、无矛盾\n\n"
        "请对以下每条文章进行评分，输出 JSON 格式：\n"
        '{"passed": bool, "overall_score": float(0-1), "feedback": "具体修改建议", '
        '"scores": {"summary_quality": float, "tags_accuracy": float, '
        '"category_appropriateness": float, "consistency": float}}'
    )

    articles_json = json.dumps(articles, ensure_ascii=False, indent=2)
    full_prompt = f"{prompt}\n\n文章列表:\n{articles_json}"

    result, usage = chat_json(full_prompt, system=SYSTEM_REVIEW, node_name="reviewer")

    passed = result.get("passed", False)
    overall_score = result.get("overall_score", 0.0)
    feedback = result.get("feedback", "")
    scores = result.get("scores", {})

    logger.info("[Reviewer] 审核完成：passed=%s, overall_score=%.2f", passed, overall_score)
    logger.info("[Reviewer] 各维度得分: summary=%.2f tags=%.2f category=%.2f consistency=%.2f",
                 scores.get("summary_quality", 0),
                 scores.get("tags_accuracy", 0),
                 scores.get("category_appropriateness", 0),
                 scores.get("consistency", 0))

    return {
        "review_passed": passed,
        "review_feedback": feedback,
        "iteration": iteration + 1,
        "cost_tracker": accumulate_usage(state.get("cost_tracker", {}), usage),
    }


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
    """
    analyses = state.get("analyses", [])

    logger.info("[Organizer] 开始整理并保存 %d 条 analyses...", len(analyses))

    articles = [a for a in analyses if a.get("relevance_score", 0) >= 0.6]
    logger.info("[Organizer] 过滤后（score>=0.6）：%d 条", len(articles))

    before_dedup = len(articles)
    articles = _dedup_by_url(articles)
    logger.info("[Organizer] 去重后：%d 条（移除 %d 条重复）", len(articles), before_dedup - len(articles))

    for idx, article in enumerate(articles):
        if "id" not in article:
            article["id"] = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{idx:03d}"
        if "source" not in article:
            article["source"] = "github"
        if "collected_at" not in article:
            article["collected_at"] = datetime.now(timezone.utc).isoformat()

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    saved_ids = []

    for article in articles:
        article_id = article.get("id")
        if not article_id:
            continue

        file_path = ARTICLES_DIR / f"{article_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(article, f, ensure_ascii=False, indent=2)

        saved_ids.append(article_id)
        logger.info("[Organizer] 已保存: %s", article_id)

    _update_index(articles)

    logger.info("[Organizer] 整理保存完成，共 %d 条，已更新索引", len(saved_ids))
    return {"saved_ids": saved_ids}


FEEDBACKS = [
    "摘要过于笼统，缺乏具体技术细节，请补充更精准的描述。",
    "标签覆盖面不足，缺少相关技术栈关键词，建议增加 2-3 个标签。",
]


def review_node_test(state: KBState) -> dict:
    """测试用审核节点：前 2 次强制不通过，第 3 次通过。"""
    iteration = state.get("iteration", 0)

    logger.info("[Reviewer] 测试审核（iteration=%d）", iteration)

    if iteration >= 2:
        logger.info("[Reviewer] iteration=%d, review_passed=True", iteration)
        return {
            "review_passed": True,
            "review_feedback": "",
            "iteration": iteration + 1,
        }

    feedback = FEEDBACKS[iteration] if iteration < len(FEEDBACKS) else "请修正后重新提交。"
    logger.info("[Reviewer] iteration=%d, review_passed=False, feedback=%s", iteration, feedback)

    return {
        "review_passed": False,
        "review_feedback": feedback,
        "iteration": iteration + 1,
    }