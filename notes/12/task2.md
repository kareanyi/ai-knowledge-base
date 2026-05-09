## 理解代码

```shell
1. 关于 must_contain_any
我的代码里没有用 must_contain_any，用的是直接断言：
assert exp["has_summary"] is True
assert "summary" in result
assert len(result["summary"]) >= exp["summary_min_length"]
这是因为 expected 里已经预设了检查条件，直接比对更直观。你是想问为什么不设计成通用的集合运算 helper？
---
2. pytest.mark.slow 的作用
@pytest.mark.slow
def test_llm_judge_analysis():
    ...
- 标记需要真实 LLM 调用的测试
- 可用 pytest -m "not slow" 跳过，快速验证结构
- 本地 CI / 无 API Key 时跑结构测试，不跑耗钱的 LLM 测试
---
3. LLM-as-Judge 的原理和可靠性
原理：让一个 LLM（裁判）评估另一个 LLM（分析器）的输出质量，输出 1-10 分数。
优点：
- 避免人工标注，快速批量评估
- 能捕捉"语法正确但语义空洞"等问题
局限性：
- 裁判 LLM 本身有偏见（偏爱冗长、正式的回答）
- 两次 LLM 调用叠加，成本翻倍
- 分数阈值（>=5）是经验值，需根据业务调整
适合：内部开发迭代时的相对比较，而非生产环境的绝对质量判断。
---
4. 为什么 test_eval_cases_structure 不调 LLM？
因为它是纯结构验证，目的有二：
1. 提前失败（Fail Fast）：结构有问题时直接报错，不用等到 LLM 调用才发现 case 定义缺字段
2. 节省成本：不调 LLM 就能验证 EVAL_CASES 列表是否完整（>=3个、每个都有 name/input/expected）
结构验证（快） → LLM 分析（慢/贵） → Judge 评估（更慢/更贵）
符合测试金字塔原则：大量低成本的结构测试，少量昂贵的 LLM 集成测试。
```

## 本地验证

```shell
millerlin@millerdeMacBook-Pro v3 % uv run pytest tests/eval_test.py
warning: No `requires-python` value found in the workspace. Defaulting to `>=3.14`.
============================================================================================================================ test session starts =============================================================================================================================
platform darwin -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/millerlin/Codes/local/opencode-workspace/action-camp/ai-knowledge-base/v3
configfile: pyproject.toml
plugins: langsmith-0.8.2, anyio-4.13.0
collected 6 items / 4 deselected / 2 selected

tests/eval_test.py ..                                                                                                                                                                                                                                                  [100%]

====================================================================================================================== 2 passed, 4 deselected in 0.03s =======================================================================================================================
millerlin@millerdeMacBook-Pro v3 % uv run pytest tests/eval_test.py -m slow
warning: No `requires-python` value found in the workspace. Defaulting to `>=3.14`.
============================================================================================================================ test session starts =============================================================================================================================
platform darwin -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/millerlin/Codes/local/opencode-workspace/action-camp/ai-knowledge-base/v3
configfile: pyproject.toml
plugins: langsmith-0.8.2, anyio-4.13.0
collected 6 items / 2 deselected / 4 selected

tests/eval_test.py FF..                                                                                                                                                                                                                                                [100%]

================================================================================================================================== FAILURES ==================================================================================================================================
__________________________________________________________________________________________________________________________ test_llm_judge_analysis ___________________________________________________________________________________________________________________________

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

>       assert score >= 5, f"LLM judge score {score} < 5，分析质量不达标"
E       AssertionError: LLM judge score 0 < 5，分析质量不达标
E       assert 0 >= 5

tests/eval_test.py:131: AssertionError
______________________________________________________________________________________________________________________ test_llm_positive_case_analysis _______________________________________________________________________________________________________________________

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
>       assert len(result["tech_stack"]) > 0
E       assert 0 > 0
E        +  where 0 = len([])

tests/eval_test.py:152: AssertionError
========================================================================================================================== short test summary info ===========================================================================================================================
FAILED tests/eval_test.py::test_llm_judge_analysis - AssertionError: LLM judge score 0 < 5，分析质量不达标
FAILED tests/eval_test.py::test_llm_positive_case_analysis - assert 0 > 0
============================================================================================================ 2 failed, 2 passed, 2 deselected in 64.16s (0:01:04) ============================================================================================================
millerlin@millerdeMacBook-Pro v3 %
```