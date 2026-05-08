"""Reviewer 节点 - 质量审核。

审核对象是 state["analyses"]（Analyzer 输出），
不是 articles（Organizer 输出）。
"""

import logging

from .model_client import chat_json, accumulate_usage
from .state import KBState

logger = logging.getLogger(__name__)

SYSTEM_REVIEW = "你是一个严格的质量审核员，负责对 AI 技术条目进行五维度评分。响应末尾必须用 ===JSON_START=== 和 ===JSON_END=== 包裹纯 JSON 输出，不要包含思考过程。"

DIMENSION_WEIGHTS = {
    "summary_quality": 0.25,
    "technical_depth": 0.25,
    "relevance": 0.20,
    "originality": 0.15,
    "formatting": 0.15,
}

PASS_THRESHOLD = 7.0
MAX_REVIEW_ITEMS = 5


MAX_REVIEW_RETRIES = 2


def review_node(state: KBState) -> dict:
    """审核节点：对 analyses 进行五维度评分，计算加权总分。

    Args:
        state: KBState，包含 plan, analyses, iteration, cost_tracker

    Returns:
        dict: review_passed, review_feedback, iteration, cost_tracker
    """
    analyses = state.get("analyses", [])
    iteration = state.get("iteration", 0)
    cost_tracker = state.get("cost_tracker", {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_cost_yuan": 0.0,
    })

    logger.info("[Reviewer] 开始审核 %d 条 analyses（iteration=%d）...", len(analyses), iteration)

    if not analyses:
        logger.info("[Reviewer] 无 analyses 数据，自动通过")
        return {
            "review_passed": True,
            "review_feedback": "",
            "iteration": iteration,
            "cost_tracker": cost_tracker,
        }

    target = analyses[:MAX_REVIEW_ITEMS]
    logger.info("[Reviewer] 限制审核前 %d 条（控 token 消耗）", len(target))

    prompt = _build_review_prompt(target)

    result = None
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    last_error = ""

    for attempt in range(MAX_REVIEW_RETRIES + 1):
        try:
            result, usage = chat_json(prompt, system=SYSTEM_REVIEW, temperature=0.1)
            cost_tracker = accumulate_usage(cost_tracker, usage)
        except Exception as e:
            last_error = str(e)
            logger.warning("[Reviewer] LLM 调用失败（尝试 %d/%d）: %s",
                           attempt + 1, MAX_REVIEW_RETRIES + 1, e)
            if attempt < MAX_REVIEW_RETRIES:
                continue
            return {
                "review_passed": True,
                "review_feedback": f"LLM 调用失败（{last_error}），自动通过",
                "iteration": iteration,
                "cost_tracker": cost_tracker,
            }

        if not isinstance(result, (dict, list)):
            last_error = f"返回类型错误: {type(result).__name__}"
            logger.warning("[Reviewer] %s（尝试 %d/%d）",
                           last_error, attempt + 1, MAX_REVIEW_RETRIES)
            if attempt < MAX_REVIEW_RETRIES:
                continue
            return {
                "review_passed": True,
                "review_feedback": f"LLM 返回格式错误（{last_error}），自动通过",
                "iteration": iteration,
                "cost_tracker": cost_tracker,
            }

        if isinstance(result, list):
            if not result or not isinstance(result[0], dict):
                last_error = f"返回空数组或元素不是 dict"
                logger.warning("[Reviewer] %s（尝试 %d/%d）",
                               last_error, attempt + 1, MAX_REVIEW_RETRIES)
                if attempt < MAX_REVIEW_RETRIES:
                    continue
                return {
                    "review_passed": True,
                    "review_feedback": f"LLM 返回格式错误（{last_error}），自动通过",
                    "iteration": iteration,
                    "cost_tracker": cost_tracker,
                }
            logger.info("[Reviewer] 收到 %d 条审核结果的数组，计算平均分", len(result))
            scores_list = [item.get("scores", {}) for item in result if isinstance(item.get("scores"), dict)]
            if not scores_list:
                last_error = "scores 全都不是 dict"
                logger.warning("[Reviewer] %s（尝试 %d/%d）",
                               last_error, attempt + 1, MAX_REVIEW_RETRIES)
                if attempt < MAX_REVIEW_RETRIES:
                    continue
                return {
                    "review_passed": True,
                    "review_feedback": f"LLM 返回格式错误（{last_error}），自动通过",
                    "iteration": iteration,
                    "cost_tracker": cost_tracker,
                }
            avg_scores = {}
            for dim in DIMENSION_WEIGHTS:
                avg_scores[dim] = sum(s.get(dim, 0) for s in scores_list) / len(scores_list)
            weighted_score = sum(avg_scores[dim] * weight for dim, weight in DIMENSION_WEIGHTS.items())
            review_passed = weighted_score >= PASS_THRESHOLD
            feedback = "; ".join(f"条目{i+1}: {item.get('feedback', '')}" for i, item in enumerate(result) if item.get('feedback'))
            scores = avg_scores
        else:
            scores = result.get("scores", {})
            if not isinstance(scores, dict):
                last_error = f"scores 类型错误: {type(scores).__name__}"
                logger.warning("[Reviewer] %s（尝试 %d/%d）",
                               last_error, attempt + 1, MAX_REVIEW_RETRIES)
                if attempt < MAX_REVIEW_RETRIES:
                    continue
                return {
                    "review_passed": True,
                    "review_feedback": f"LLM 返回格式错误（{last_error}），自动通过",
                    "iteration": iteration,
                    "cost_tracker": cost_tracker,
                }
            weighted_score = _compute_weighted_score(result)
            review_passed = weighted_score >= PASS_THRESHOLD
            feedback = result.get("feedback", "")

        break

    logger.info(
        "[Reviewer] 加权总分=%.2f（阈值=%.1f），passed=%s",
        weighted_score, PASS_THRESHOLD, review_passed,
    )
    logger.info(
        "[Reviewer] 各维度得分: summary=%.1f technical=%.1f relevance=%.1f "
        "originality=%.1f formatting=%.1f",
        scores.get("summary_quality", 0),
        scores.get("technical_depth", 0),
        scores.get("relevance", 0),
        scores.get("originality", 0),
        scores.get("formatting", 0),
    )

    return {
        "review_passed": review_passed,
        "review_feedback": feedback,
        "iteration": iteration + 1,
        "cost_tracker": cost_tracker,
    }


def _build_review_prompt(analyses: list[dict]) -> str:
    """构建审核 prompt。"""
    dimensions = [
        ("summary_quality", "摘要质量", "摘要是否准确、简洁、有信息量，25%"),
        ("technical_depth", "技术深度", "是否包含足够的技术细节和实现原理，25%"),
        ("relevance", "相关性", "与 AI/LLM/Agent 领域的相关程度，20%"),
        ("originality", "原创性", "内容是否独特、是否有见解，15%"),
        ("formatting", "格式规范", "JSON 结构是否规范、字段是否完整，15%"),
    ]

    dim_lines = "\n".join(
        f"- {key}: {label}（权重 {weight}）"
        for key, label, weight in dimensions
    )

    analyses_json = __import__("json").dumps(analyses, ensure_ascii=False, indent=2)

    return (
        "你是一个严格的质量审核员。请对以下 AI 技术条目进行**逐条**五维度评分。\n\n"
        f"评分维度（每维 1-10 分）：\n{dim_lines}\n\n"
        "加权总分 = sum(score * weight)，满分 10 分，>=7.0 分视为通过。\n\n"
        "请在响应末尾用以下分隔符包裹纯 JSON 输出，不要包含任何思考过程：\n"
        "===JSON_START===\n"
        "<这里放JSON>\n"
        "===JSON_END===\n\n"
        "JSON 格式：\n"
        '[{"passed": bool, "feedback": "该条目的具体修改建议", '
        '"scores": {"summary_quality": float, "technical_depth": float, '
        '"relevance": float, "originality": float, "formatting": float}}]\n\n'
        "注意：返回数组，不要返回单个对象。数组长度必须等于条目数量。\n\n"
        f"待审核条目（JSON 数组，共 {len(analyses)} 条）：\n{analyses_json}"
    )


def _compute_weighted_score(result: dict) -> float:
    """用代码计算加权总分，不信任 LLM 算术。

    Args:
        result: chat_json 返回的解析结果

    Returns:
        加权总分（0-10）
    """
    scores = result.get("scores", {})
    if not isinstance(scores, dict):
        logger.warning("[Reviewer] scores 类型错误: %s（期望 dict），返回 0", type(scores).__name__)
        return 0.0
    total = 0.0
    for dim, weight in DIMENSION_WEIGHTS.items():
        score = scores.get(dim, 0)
        total += score * weight
    return total