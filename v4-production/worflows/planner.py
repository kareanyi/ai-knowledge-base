"""Planner 策略节点。

根据目标采集量自动选择采集策略（lite/standard/full），
返回策略参数供下游节点使用。
"""

import logging
import os

from .state import KBState

logger = logging.getLogger(__name__)

DEFAULT_TARGET = 10


def plan_strategy(target_count: int | None = None) -> dict:
    """根据目标采集量返回对应策略。

    Args:
        target_count: 目标采集量，不传则从环境变量 PLANNER_TARGET_COUNT 读取，默认 10。

    Returns:
        策略字典，包含 per_source_limit, relevance_threshold, max_iterations, tier, rationale。
    """
    if target_count is None:
        target_count = int(os.getenv("PLANNER_TARGET_COUNT", DEFAULT_TARGET))

    if target_count < 10:
        tier = "lite"
        strategy = {
            "tier": tier,
            "per_source_limit": 5,
            "relevance_threshold": 0.7,
            "max_iterations": 1,
            "rationale": (
                "目标采集量 < 10，采用 lite 策略：限制每个数据源最多 5 条，"
                " relevance阈值设为较高的 0.7 以确保内容质量，仅执行 1 次迭代，"
                " 降低 LLM 调用成本，适合轻量采集场景。"
            ),
        }
    elif target_count < 20:
        tier = "standard"
        strategy = {
            "tier": tier,
            "per_source_limit": 10,
            "relevance_threshold": 0.5,
            "max_iterations": 2,
            "rationale": (
                "目标采集量在 10-19 之间，采用 standard 策略：每源限制 10 条，"
                " relevance阈值设为 0.5 以平衡质量与数量，允许 2 次迭代进行质量审核，"
                " 适合常规采集任务。"
            ),
        }
    else:
        tier = "full"
        strategy = {
            "tier": tier,
            "per_source_limit": 20,
            "relevance_threshold": 0.4,
            "max_iterations": 3,
            "rationale": (
                "目标采集量 >= 20，采用 full 策略：每源限制 20 条，"
                " relevance阈值放宽至 0.4 以收集更多候选内容，"
                " 允许 3 次迭代进行深度质量审核和反馈修正，适合大规模采集任务。"
            ),
        }

    logger.info("[Planner] 目标采集量=%d，选择策略 tier=%s", target_count, tier)
    return strategy


def planner_node(state: KBState) -> dict:
    """LangGraph 节点：调用 plan_strategy 并返回 {"plan": plan}。

    Args:
        state: LangGraph 工作流状态（KBState）。

    Returns:
        包含 plan 键的字典，更新状态中的 plan 字段。
    """
    target_count = state.get("target_count")
    plan = plan_strategy(target_count)
    logger.info("[Planner] 生成策略: tier=%s, per_source_limit=%d, "
                 "relevance_threshold=%.1f, max_iterations=%d",
                 plan["tier"], plan["per_source_limit"],
                 plan["relevance_threshold"], plan["max_iterations"])
    return {"plan": plan}