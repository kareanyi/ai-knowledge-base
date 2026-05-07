# AI 知识库 · 编码规范 v0.3

## 要做什么
- Python 用 **black==24.4.0** 格式化，TS 用 **prettier**，统一 **UTF-8**，Python 版本 **>=3.12**
- TypeScript 明确 `strict: true` + `noUncheckedIndexedAccess: true`
- 所有公开函数必须有 **Google style docstring**（`pydocstyle` CI 检测）
- 禁止硬编码业务常量，字面值抽成 `constants.py` 或枚举
- Python 类型检查用 `mypy --strict`
- 自定义异常基类 `BaseAppError`，禁止裸 `except`
- 所有日志用 `log` 模块，`print()` 仅限 `__main__`
- 依赖用 `pyproject.toml`，import 用 `isort` 统一顺序
- commit message 用 **Conventional Commits**
- 任何看起来像 secret 的字面值是**红线**

## 不做什么
- 不用任何魔法字符串
- 不允许 TODO 提交到 main（PR to main 时拦截）
- 禁止裸 `except`
- 禁止 `print()` 用于业务日志

## 边界 & 验收
| 层级 | 覆盖率 |
|------|--------|
| 业务逻辑层 | >= 90% |
| 工具层 | >= 80% |
| 边界适配层 | >= 50% |

## 怎么验证
```bash
# CI
ruff check . && ruff format --check . && mypy . && pytest --cov --cov-fail-under=80
check-jsonschema knowledge/**/*.json
```
