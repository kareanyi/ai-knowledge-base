"""LangGraph 工作流共享状态定义。

定义 KBState 类作为整个工作流的通信载体，
各 Agent 通过读写状态中的结构化摘要进行协作，而非直接传递原始数据。
"""

from typing import TypedDict


class KBState(TypedDict, total=False):
    """知识库工作流的共享状态。

    遵循"报告式通信"原则：状态中的每个字段都是结构化摘要，
    而非原始数据。各 Agent 负责将原始数据提炼为摘要后写入状态，
    下一环节直接消费摘要，无需重复处理。

    Attributes:
        sources: 采集阶段输出的原始条目列表。
            数据格式: list[dict]，每项包含 url, title, description, stars 等原始字段。
            此字段仅作暂存，Analyzer 会消费后丢弃原始内容，仅保留分析结果。
        analyses: LLM 逐条分析后的结构化结果列表。
            数据格式: list[dict]，每项包含 summary, tech_stack, tags, problem_solved 等 AI 生成字段。
            由 Analyzer 写入，Organizer 消费后进行去重合并。
        articles: 经过质量审核、去重、标签规范化后的最终知识条目列表。
            数据格式: list[dict]，每项为符合 knowledge 条目 JSON Schema 的完整记录。
            仅包含可直接发布的条目，status 字段为 published 或 archived。
        review_feedback: 审核节点对当前 articles 的反馈意见。
            数据格式: str，由 Organizer 或人工审核者写入。
            包含具体修改建议，供 Analyzer 重新分析时参考。
        review_passed: 当前 articles 是否通过审核。
            数据格式: bool，True 表示可以发布，False 表示需要迭代。
            达到最大迭代次数后强制结束。
        iteration: 当前审核循环的轮次。
            数据格式: int，初始值为 0，每次 review 后 +1。
            超过 3 次时强制结束，保留当前结果。
        cost_tracker: 各阶段 LLM 调用的 token 消耗汇总。
            数据格式: dict，包含 prompt_tokens, completion_tokens, total_cost_yuan 等累计字段。
            供审计和成本控制使用。
    """

    sources: list[dict]
    analyses: list[dict]
    articles: list[dict]
    review_feedback: str
    review_passed: bool
    iteration: int
    cost_tracker: dict