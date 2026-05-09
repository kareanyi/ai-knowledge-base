## 理解代码

```shell
设计解释
1. 成本计算公式：tokens * price / 1_000_000
定价单位是每百万 tokens，所以：
- 1000 tokens → 1000/1_000_000 = 0.001 百万tokens
- 0.001 百万 × $2/百万 = $0.002
这是行业惯例（OpenAI、Claude 等都按百万 tokens 报价）。
---
2. record() 和 check() 为什么分开？
职责分离：
- record() 是observer，只负责记录，不做判断
- check() 是judge，只做预算判断
分开的好处：
1. 批量记录后统一检查：一次 LLM 调用后立即检查会频繁中断；可以在关键节点（每个 node 结束后）统一 check
2. 灵活性：允许先累积多条记录，再决定是否继续
3. 可测试性：独立验证记录逻辑和检查逻辑
---
3. 为什么 check() 超标时抛异常而不是返回 False？
因为预算超标是不可恢复的错误：
- 返回 False → 调用方可以忽略（if not guard.check(): pass）
- 抛异常 → 调用方必须处理，无法静默忽略
成本超支是系统级错误，工作流应该立即停止而不是继续执行浪费更多预算。抛出 BudgetExceededError 确保预算保护不被绕过。
---
4. 在 LangGraph 工作流中集成
在 workflows/state.py 的 KBState 中增加 cost_guard 字段，然后在各 node 函数中调用：
# workflows/state.py
@dataclass
class KBState(TypedDict):
    ...
    cost_guard: CostGuard  # 新增
# workflows/analyzer.py
def analyze_node(state: KBState) -> KBState:
    guard = state["cost_guard"]
    result = call_llm(...)
    guard.record("analyzer", result["usage"], model=result["model"])
    guard.check()  # 超限抛异常中断工作流
    return state
# workflows/graph.py 入口处
from tests.cost_guard import CostGuard
def build_graph():
    guard = CostGuard(
        budget_yuan=float(os.getenv("MONTHLY_BUDGET", 10.0)),
        alert_threshold=0.8,
    )
    # 初始状态注入 guard
    initial_state = {"cost_guard": guard, ...}
    return compiled_graph.invoke(initial_state)
关键点：*每个 node 执行后 record() + check()*，既追踪成本又保护预算。
```

## 运行测试

```shell
millerlin@millerdeMacBook-Pro v3 % uv run python3 tests/cost_guard.py
test_alert_threshold (__main__.TestCostGuard.test_alert_threshold) ... ok
test_budget_exceeded (__main__.TestCostGuard.test_budget_exceeded) ... ok
test_cost_tracking (__main__.TestCostGuard.test_cost_tracking) ... ok
test_multiple_records (__main__.TestCostGuard.test_multiple_records) ... ok
test_report_generation (__main__.TestCostGuard.test_report_generation) ... ok
test_save_report (__main__.TestCostGuard.test_save_report) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.007s

OK
```