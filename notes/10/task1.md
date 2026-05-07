## 安装

```shell
millerlin@millerdeMacBook-Pro v3 % uv run python -c "from langgraph.version import __version__; print(__version__)"
1.1.10
millerlin@millerdeMacBook-Pro v3 %
```

##验证KBState

```shell
millerlin@millerdeMacBook-Pro v3 % uv run python -c "
from workflows.state import KBState

# 检查字段定义
annotations = KBState.__annotations__
print('KBState 字段：')
for name, type_hint in annotations.items():
    print(f'  {name}: {type_hint}')
print(f'\n共 {len(annotations)} 个字段')

# 创建一个实例
state: KBState = {
    'sources': [],
    'analyses': [],
    'articles': [],
    'review_feedback': '',
    'review_passed': False,
    'iteration': 0,
    'cost_tracker': {},
}
print(f'实例创建成功，iteration = {state[\"iteration\"]}')
"
KBState 字段：
  sources: list[dict]
  analyses: list[dict]
  articles: list[dict]
  review_feedback: <class 'str'>
  review_passed: <class 'bool'>
  iteration: <class 'int'>
  cost_tracker: <class 'dict'>

共 7 个字段
实例创建成功，iteration = 0
```