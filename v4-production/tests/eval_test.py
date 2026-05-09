"""评估测试：验证 AI 知识库分析质量。

用法：
    pytest tests/eval_test.py              # 本地验证（默认，跳过 slow）
    pytest tests/eval_test.py -m slow     # LLM 测试
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

import pytest

warnings.filterwarnings("ignore", category=pytest.PytestUnknownMarkWarning)

from workflows.model_client import chat


EVAL_CASES: list[dict] = [
    {
        "name": "正面案例_技术文章",
        "input": {
            "title": "GPT-4.1：多模态大模型的最新进展",
            "source": "github_trending",
            "source_url": "https://github.com/openai/gpt-4.1",
            "description": "OpenAI 发布 GPT-4.1，在视觉理解和长文本处理方面有显著提升，支持 128K context window，在多项基准测试中刷新 SOTA。",
        },
        "expected": {
            "has_summary": True,
            "has_tags": True,
            "tech_stack_not_empty": True,
            "summary_min_length": 10,
        },
    },
    {
        "name": "负面案例_无关内容",
        "input": {
            "title": "Best Pizza in New York",
            "source": "hacker_news",
            "source_url": "https://news.ycombinator.com/item?id=123",
            "description": "This is a discussion about the best pizza places to visit in NYC, including recommendations from local food bloggers.",
        },
        "expected": {
            "is_low_relevance": True,
            "relevance_score_max": 4,
        },
    },
    {
        "name": "边界案例_极短输入",
        "input": {
            "title": "AI",
            "source": "github_trending",
            "source_url": "https://github.com/trending",
            "description": "AI",
        },
        "expected": {
            "no_crash": True,
            "summary_min_length": 0,
        },
    },
]


def _run_analysis(item: dict) -> dict:
    """调用 LLM 分析单条输入，返回结构化结果。"""
    prompt = f"""你是一个专业的 AI 技术分析师。请分析以下条目，输出 JSON：

{{
    "summary": "一句话描述该项目，不足 10 字则补充完整",
    "tech_stack": ["技术栈列表"],
    "tags": ["标签列表"],
    "relevance_score": 1-10 的整数，表示与 AI/LLM/Agent 领域的相关度"
}}

条目信息：
- 标题：{item['title']}
- 来源：{item['source']}
- 链接：{item['source_url']}
- 描述：{item['description']}

只输出 JSON，不要其他内容。"""
    system = "你是一个专业的 AI 技术分析师。请用 JSON 格式回复。"
    text, usage = chat(prompt, system=system)
    import json

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {"summary": text[:200], "tech_stack": [], "tags": [], "relevance_score": 1}
    result["_usage"] = usage
    return result


@pytest.mark.slow
def test_llm_judge_analysis():
    """LLM-as-Judge 测试：让 LLM 对分析结果打分，断言分数 >= 5。"""
    case = EVAL_CASES[0]
    item = case["input"]
    result = _run_analysis(item)

    judge_prompt = f"""你是一个严格的 AI 技术分析师评审。请评估以下分析结果的质量，给出 1-10 的评分。

评分标准：
- 8-10：摘要精准、技术栈正确、标签合理
- 5-7：基本合格，但有改进空间
- 1-4：质量较差，需要重新分析

分析结果：
- 标题：{item['title']}
- 摘要：{result.get('summary', '')}
- 技术栈：{result.get('tech_stack', [])}
- 标签：{result.get('tags', [])}
- 相关度评分：{result.get('relevance_score', 'N/A')}

请只输出一个整数（1-10）表示你的评分，不要其他内容。"""

    judge_text, _ = chat(judge_prompt, system="你是一个严格的评审。")
    try:
        score = int(judge_text.strip())
    except ValueError:
        score = 0

    assert score >= 5, f"LLM judge score {score} < 5，分析质量不达标"


@pytest.mark.slow
def test_llm_positive_case_analysis():
    """正面案例：技术文章输入，预期有摘要、有关键词。"""
    case = EVAL_CASES[0]
    result = _run_analysis(case["input"])
    exp = case["expected"]

    assert exp["has_summary"] is True
    assert "summary" in result
    assert len(result["summary"]) >= exp["summary_min_length"]

    assert exp["has_tags"] is True
    assert "tags" in result
    assert isinstance(result["tags"], list)

    assert exp["tech_stack_not_empty"] is True
    assert "tech_stack" in result
    assert isinstance(result["tech_stack"], list)
    assert len(result["tech_stack"]) > 0


@pytest.mark.slow
def test_llm_negative_case_filtering():
    """负面案例：无关内容输入，预期被过滤或标记为低相关。"""
    case = EVAL_CASES[1]
    result = _run_analysis(case["input"])
    exp = case["expected"]

    score = result.get("relevance_score", 10)
    assert score <= exp["relevance_score_max"], f"负面案例相关性分数 {score} 过高，应 <= {exp['relevance_score_max']}"


@pytest.mark.slow
def test_llm_edge_case_no_crash():
    """边界案例：极短输入（如"AI"），预期不崩溃。"""
    case = EVAL_CASES[2]
    result = _run_analysis(case["input"])
    exp = case["expected"]

    assert exp["no_crash"] is True
    assert "summary" in result
    assert len(result["summary"]) >= exp["summary_min_length"]


def test_eval_cases_structure():
    """本地验证（不调用 LLM）：验证 EVAL_CASES 结构完整性。"""
    assert len(EVAL_CASES) >= 3, f"EVAL_CASES 应至少包含 3 个案例，当前只有 {len(EVAL_CASES)} 个"

    for case in EVAL_CASES:
        assert "name" in case, f"案例缺少 name 字段: {case}"
        assert "input" in case, f"案例 {case['name']} 缺少 input 字段"
        assert "expected" in case, f"案例 {case['name']} 缺少 expected 字段"

        inp = case["input"]
        assert "title" in inp, f"案例 {case['name']} 的 input 缺少 title"
        assert "source" in inp, f"案例 {case['name']} 的 input 缺少 source"
        assert "source_url" in inp, f"案例 {case['name']} 的 input 缺少 source_url"
        assert "description" in inp, f"案例 {case['name']} 的 input 缺少 description"

        exp = case["expected"]
        assert isinstance(exp, dict), f"案例 {case['name']} 的 expected 应为 dict"
        assert len(exp) > 0, f"案例 {case['name']} 的 expected 不能为空"


def test_chat_function_signature():
    """验证 chat() 函数签名和返回值类型（不调用 LLM）。"""
    import inspect

    sig = inspect.signature(chat)
    params = list(sig.parameters.keys())
    assert "prompt" in params, f"chat() 应有 prompt 参数，当前参数: {params}"
    assert "system" in params, f"chat() 应有 system 参数，当前参数: {params}"

    ret_annotation = sig.return_annotation
    assert ret_annotation != inspect.Parameter.empty, "chat() 应有返回值注解"
