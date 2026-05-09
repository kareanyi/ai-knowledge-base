"""Reviser 节点 - 根据审核反馈修改 analyses。

接收 state["analyses"] 和 state["review_feedback"]，
将反馈注入修改 prompt，调用 LLM 返回改进后的 analyses 列表。
"""

import json
import logging

from .model_client import chat_json, accumulate_usage, JSONTruncatedError, BudgetExceededError
from .state import KBState

logger = logging.getLogger(__name__)

SYSTEM_REVISE = "你是一个专业的 AI 技术分析师，负责根据审核反馈修正分析结果，使其更准确、质量更高。响应末尾必须用 ===JSON_START=== 和 ===JSON_END=== 包裹纯 JSON 输出，不要包含任何思考过程。"

MAX_REVISE_RETRIES = 2


def revise_node(state: KBState) -> dict:
    """修订节点：根据审核反馈修改 analyses。

    Args:
        state: KBState，包含 analyses, review_feedback, iteration, cost_tracker

    Returns:
        dict: improved analyses, iteration, cost_tracker
    """
    analyses = state.get("analyses", [])
    feedback = state.get("review_feedback", "")
    iteration = state.get("iteration", 0)
    cost_tracker = state.get(
        "cost_tracker",
        {"prompt_tokens": 0, "completion_tokens": 0, "total_cost_yuan": 0.0},
    )

    logger.info("[Reviser] 开始修订 %d 条 analyses...", len(analyses))

    if not analyses:
        logger.info("[Reviser] 无 analyses 数据，跳过修订")
        return {}

    if not feedback:
        logger.info("[Reviser] 无 review_feedback，跳过修订")
        return {}

    analyses_json = json.dumps(analyses, ensure_ascii=False, indent=2)

    prompt = (
        "你是一个专业的 AI 技术分析师。请根据以下审核反馈，对每条分析结果进行修正。\n\n"
        f"审核反馈:\n{feedback}\n\n"
        "请对每条条目进行修改，保持 JSON 结构不变，只修正有问题的部分。\n\n"
        "【重要】你必须而且只能返回一个 JSON 数组，不要返回任何其他格式。\n"
        "不要返回单个对象，不要返回包含 scores 字段的对象，必须是 JSON 数组。\n"
        "每个数组元素必须是对应输入条目的修正版本，保持相同顺序。\n\n"
        "请在响应末尾用以下分隔符包裹纯 JSON 输出，不要包含任何思考过程：\n"
        "===JSON_START===\n"
        "[{...}, {...}, ...]\n"
        "===JSON_END===\n\n"
        f"待修订条目（JSON 数组，共 {len(analyses)} 条）：\n{analyses_json}"
    )

    result = None
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    last_error = ""

    for attempt in range(MAX_REVISE_RETRIES + 1):
        try:
            result, usage = chat_json(prompt, system=SYSTEM_REVISE, temperature=0.4, node_name="reviser")
            cost_tracker = accumulate_usage(cost_tracker, usage)
        except BudgetExceededError:
            raise
        except Exception as e:
            last_error = str(e)
            logger.warning("[Reviser] LLM 调用失败（重试 %d/%d, iteration=%d）: %s",
                           attempt + 1, MAX_REVISE_RETRIES + 1, iteration, e)
            if attempt < MAX_REVISE_RETRIES:
                continue
            return {"analyses": analyses, "cost_tracker": cost_tracker}

        if not isinstance(result, list):
            last_error = f"返回类型错误: {type(result).__name__}"
            logger.warning("[Reviser] %s（重试 %d/%d, iteration=%d）",
                           last_error, attempt + 1, MAX_REVISE_RETRIES, iteration)
            if attempt < MAX_REVISE_RETRIES:
                continue
            return {"analyses": analyses, "cost_tracker": cost_tracker}

        if len(result) != len(analyses):
            last_error = f"返回数组长度不匹配: {len(result)} vs {len(analyses)}"
            logger.warning("[Reviser] %s（重试 %d/%d, iteration=%d）",
                           last_error, attempt + 1, MAX_REVISE_RETRIES, iteration)
            if attempt < MAX_REVISE_RETRIES:
                continue
            return {"analyses": analyses, "cost_tracker": cost_tracker}

        break

    improved = result
    logger.info("[Reviser] 修订完成，共 %d 条", len(improved))
    return {"analyses": improved, "cost_tracker": cost_tracker, "iteration": iteration + 1}
