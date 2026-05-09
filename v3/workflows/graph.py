"""LangGraph 工作流图定义。

组装 collect → analyze → review → revise（循环）→ organize 的条件路由图。"""

import logging

from langgraph.graph import StateGraph, END

from workflows.collector import collect_node
from workflows.analyzer import analyze_node
from workflows.reviewer import review_node
from workflows.reviser import revise_node
from workflows.human_flag import human_flag_node
from workflows.organizer import organize_node
from workflows.planner import planner_node
from workflows.state import KBState

logger = logging.getLogger(__name__)


def route_after_review(state: KBState) -> str:
    """根据审核结果路由下一步。

    Args:
        state: 当前工作流状态。

    Returns:
        "organize" 表示通过审核，进入整理保存节点；
        "revise" 表示未通过审核且未达最大迭代，进入修订节点；
        "human_flag" 表示未通过审核且已达最大迭代，进入人工处理节点。
    """
    plan = state.get("plan", {}) or {}
    max_iteration = int(plan.get("max_iterations", 3))
    iteration = state.get("iteration", 0)
    review_passed = state.get("review_passed", False)

    logger.info("[Router] review_passed=%s, iteration=%d, max_iteration=%d", review_passed, iteration, max_iteration)

    if review_passed:
        return "organize"
    if iteration < max_iteration:
        return "revise"
    return "human_flag"


def build_graph() -> StateGraph:
    """构建并返回编译后的 LangGraph 应用。

    工作流拓扑：
        plan → collect → analyze → review ─┬─→ organize（整理+保存）→ END
                                    ├─→ revise（iter<max） → review
                                    └─→ human_flag（iter≥max）→ END

    - (true): review_passed=True → organize → END
    - (false, iter<max): review_passed=False, iteration<max → revise → review (loop)
    - (false, iter>=max): review_passed=False, iteration>=max → human_flag → END

    Returns:
        编译后的 StateGraph 应用。
    """
    graph = StateGraph(KBState)

    graph.add_node("plan", planner_node)
    graph.add_node("collect", collect_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("review", review_node)
    graph.add_node("revise", revise_node)
    graph.add_node("organize", organize_node)
    graph.add_node("human_flag", human_flag_node)

    graph.add_edge("plan", "collect")
    graph.add_edge("collect", "analyze")
    graph.add_edge("analyze", "review")

    graph.add_conditional_edges(
        "review",
        route_after_review,
        {"organize": "organize", "revise": "revise", "human_flag": "human_flag"},
    )

    graph.add_edge("revise", "review")
    graph.add_edge("organize", END)
    graph.add_edge("human_flag", END)

    graph.set_entry_point("plan")
    return graph.compile()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    app = build_graph()
    logger.info("工作流图构建完成，开始执行...")

    initial_state: KBState = {
        "sources": [],
        "analyses": [],
        "articles": [],
        "review_feedback": "",
        "review_passed": False,
        "iteration": 0,
        "cost_tracker": {"prompt_tokens": 0, "completion_tokens": 0, "total_cost_yuan": 0.0},
    }

    for event in app.stream(initial_state):
        node_name = next(iter(event.keys()), "unknown")
        node_state = event.get(node_name)
        logger.info("[Event] Node: %s", node_name)

        if node_state is None:
            logger.info("  → 节点返回空状态，跳过")
            continue

        if node_name == "collect":
            count = len(node_state.get("sources", []))
            logger.info("  → 采集到 %d 条仓库", count)
        elif node_name == "analyze":
            count = len(node_state.get("analyses", []))
            cost = node_state.get("cost_tracker", {}).get("total_cost_yuan", 0)
            logger.info("  → 分析完成 %d 条，cost=¥%.4f", count, cost)
        elif node_name == "review":
            passed = node_state.get("review_passed", False)
            iteration = node_state.get("iteration", 0)
            feedback = node_state.get("review_feedback", "")
            logger.info("  → 审核结果: passed=%s, iteration=%d, feedback=%s",
                         passed, iteration, feedback[:50] if feedback else "")
        elif node_name == "organize":
            saved = node_state.get("saved_ids", []) if node_state else []
            logger.info("  → 整理保存完成 %d 条: %s", len(saved), saved)

    logger.info("工作流执行完毕")