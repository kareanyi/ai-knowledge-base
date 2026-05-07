"""LangGraph 工作流图定义。

组装 collect → analyze → organize → review → save 的条件循环图。
"""

import logging

from langgraph.graph import StateGraph, END

from workflows.nodes import collect_node, analyze_node, organize_node, review_node, save_node
from workflows.state import KBState

logger = logging.getLogger(__name__)


def _route_after_review(state: KBState) -> str:
    """根据审核结果路由下一步。

    Args:
        state: 当前工作流状态。

    Returns:
        "save" 表示通过审核，进入保存节点；
        "organize" 表示未通过审核，回到整理节点修正。
    """
    review_passed = state.get("review_passed", False)
    iteration = state.get("iteration", 0)

    logger.info("[Router] review_passed=%s, iteration=%d", review_passed, iteration)

    if review_passed:
        return "save"
    return "organize"


def build_graph() -> StateGraph:
    """构建并返回编译后的 LangGraph 应用。

    工作流拓扑：
        collect → analyze → organize → review → save(true)
                              ↑           │
                              └──(false)──┘

        - (true): review_passed=True → save → END
        - (false): review_passed=False → organize (loop)

    Returns:
        编译后的 StateGraph 应用。
    """
    graph = StateGraph(KBState)

    graph.add_node("collect", collect_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("organize", organize_node)
    graph.add_node("review", review_node)
    graph.add_node("save", save_node)

    graph.set_entry_point("collect")

    graph.add_edge("collect", "analyze")
    graph.add_edge("analyze", "organize")
    graph.add_edge("organize", "review")

    graph.add_conditional_edges(
        "review",
        _route_after_review,
        {"save": "save", "organize": "organize"},
    )

    graph.add_edge("save", END)

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
        elif node_name == "organize":
            count = len(node_state.get("articles", []))
            logger.info("  → 整理完成 %d 条待审", count)
        elif node_name == "review":
            passed = node_state.get("review_passed", False)
            iteration = node_state.get("iteration", 0)
            feedback = node_state.get("review_feedback", "")
            logger.info("  → 审核结果: passed=%s, iteration=%d, feedback=%s",
                         passed, iteration, feedback[:50] if feedback else "")
        elif node_name == "save":
            saved = node_state.get("saved_ids", []) if node_state else []
            logger.info("  → 保存完成 %d 条: %s", len(saved), saved)

    logger.info("工作流执行完毕")