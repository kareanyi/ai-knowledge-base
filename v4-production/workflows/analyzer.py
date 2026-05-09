"""Analyzer 节点 - LLM 分析。

对采集的原始数据调用 LLM 生成结构化摘要、标签、评分。
"""

import logging

from .model_client import chat_json, accumulate_usage, BudgetExceededError
from .state import KBState

logger = logging.getLogger(__name__)

SYSTEM_ANALYZE = "你是一个专业的 AI 技术分析师，负责为每条技术条目生成结构化的中文摘要和标签。"


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
                       '"relevance_score": 0.0-1.0评分}')

    prompt = "\n".join(prompt_parts)

    system = SYSTEM_ANALYZE
    if iteration > 0 and feedback:
        system = "你是一个专业的 AI 技术分析师，负责根据审核反馈修正之前的分析结果，使其更准确、质量更高。"

    try:
        result, usage = chat_json(prompt, system=system, node_name="analyzer")
    except BudgetExceededError:
        raise
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
            "url": item.get("url", ""),
            "title": item.get("title", ""),
        }
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
    result["url"] = item.get("url", "")
    result["title"] = item.get("title", "")
    return {"item": item, "analysis": result, "usage": usage}


def analyze_node(state: KBState) -> dict:
    """分析节点：用 LLM 对每条数据生成中文摘要、标签、评分。

    Args:
        state: KBState，包含 sources, iteration, review_feedback, cost_tracker

    Returns:
        dict: analyses, cost_tracker
    """
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
        logger.info("[Analyzer] 分析进度 %d/%d（iteration=%d）", idx + 1, len(sources), iteration)

    logger.info("[Analyzer] 分析完成，共 %d 条，cost=¥%.4f",
                 len(analyses), tracker.get("total_cost_yuan", 0))
    return {"analyses": analyses, "cost_tracker": tracker}