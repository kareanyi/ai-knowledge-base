"""Supervisor 监督模式实现。

Worker 接收任务输出 JSON 格式分析报告，Supervisor 对输出进行质量审核。
审核循环：score >= 7 通过，< 7 重做，最多 3 轮，超出强制返回。
"""

import json
import logging
import re
from typing import Any

from workflows.model_client import chat

logger = logging.getLogger(__name__)


WORKER_SYSTEM = "你是一个专业的 AI 技术分析师。请以 JSON 格式输出分析报告。"
WORKER_PROMPT_TEMPLATE = '任务：{task}\n\n请分析以上任务，输出一份 JSON 格式的分析报告。'

SUPERVISOR_SYSTEM = "你是一个严格的质量审核员。请对分析报告进行评分。"
SUPERVISOR_PROMPT_TEMPLATE = """请评审以下分析报告，从三个维度评分：

1. 准确性 (1-10)：报告内容是否准确、正确
2. 深度 (1-10)：分析是否深入、有洞察力
3. 格式 (1-10)：JSON 格式是否规范、完整

分析报告内容：
{output}

请严格按以下 JSON 格式输出评分结果（不许输出其他内容）：
{{"passed": true/false, "score": int, "feedback": "具体反馈意见"}}
"""

PASS_THRESHOLD = 7


def _parse_review_result(text: str) -> dict[str, Any]:
    """解析 Supervisor 的评审结果，尝试多种容错策略。

    Args:
        text: Supervisor 返回的原始文本。

    Returns:
        解析后的评审结果字典。

    Raises:
        json.JSONDecodeError: 解析失败时。
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith("```"):
                end = i
                break
        cleaned = "\n".join(lines[start:end])

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError(f"Failed to parse review result: {text[:200]}", cleaned, 0)


def worker(task: str) -> tuple[str, dict]:
    """Worker Agent：接收任务，输出 JSON 格式的分析报告。

    Args:
        task: 分析任务描述。

    Returns:
        (json_text, usage_dict): 报告文本和 token 用量。
    """
    prompt = WORKER_PROMPT_TEMPLATE.format(task=task)
    return chat(prompt, system=WORKER_SYSTEM)


def supervisor_review(output: str) -> tuple[bool, int, str]:
    """Supervisor Agent：对 Worker 输出进行质量审核。

    Args:
        output: Worker 输出的分析报告内容。

    Returns:
        (passed, score, feedback): 是否通过、总分、反馈意见。
    """
    prompt = SUPERVISOR_PROMPT_TEMPLATE.format(output=output)
    text, usage = chat(prompt, system=SUPERVISOR_SYSTEM)
    logger.debug("Supervisor review usage: %s", usage)

    result = _parse_review_result(text)

    passed = result.get("passed", False)
    score = result.get("score", 0)
    feedback = result.get("feedback", "")

    return passed, score, feedback


def supervisor(task: str, max_retries: int = 3) -> dict[str, Any]:
    """Supervisor 监督模式主函数。

    Args:
        task: 分析任务描述。
        max_retries: 最大重试次数（默认 3）。

    Returns:
        包含以下键的字典：
        - output: 最终输出的分析报告
        - attempts: 尝试次数
        - final_score: 最终评分
        - warning: 可选的警告信息（当超过 max_retries 时提供）
    """
    warning: str | None = None
    final_score = 0
    attempts = 0

    while attempts < max_retries:
        attempts += 1

        worker_output, worker_usage = worker(task)
        logger.info("Worker attempt %d, usage: %s", attempts, worker_usage)

        passed, score, feedback = supervisor_review(worker_output)
        final_score = score
        logger.info("Supervisor review: passed=%s, score=%d, feedback=%s", passed, score, feedback)

        if passed:
            return {
                "output": worker_output,
                "attempts": attempts,
                "final_score": final_score,
            }

        if attempts < max_retries:
            task = f"{task}\n\n[审核反馈] {feedback}\n\n请根据反馈重新分析并输出 JSON 格式的报告。"

    warning = f"超过最大重试次数 ({max_retries})，强制返回结果"
    logger.warning(warning)

    return {
        "output": worker_output,
        "attempts": attempts,
        "final_score": final_score,
        "warning": warning,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

#     test_task = "分析 GitHub Trending 上一个关于 AI Agent 的热门项目"
    test_task = "请分析 LangGraph 框架的优缺点和适用场景"
    print(f"Task: {test_task}")
    print("-" * 50)

    result = supervisor(test_task)
    print("\n=== Final Result ===")
    print(f"Attempts: {result['attempts']}")
    print(f"Final Score: {result['final_score']}")
    if result.get("warning"):
        print(f"Warning: {result['warning']}")
    print(f"\nOutput:\n{result['output']}")