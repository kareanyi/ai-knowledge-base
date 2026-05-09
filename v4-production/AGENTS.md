# AI 知识库助手 - AGENTS.md

## 项目概述

AI 知识库助手自动从 GitHub Trending 和 Hacker News 采集 AI/LLM/Agent 领域的技术动态，经 AI 分析后结构化存储为 JSON 格式的知识条目，并支持多渠道分发（Telegram/飞书）。

---

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.12 |
| 模型 | OpenCode + 国产大模型（通义/智谱/DeepSeek） |
| 编排 | LangGraph |
| 抓取 | OpenClaw（浏览器自动化） |
| 存储 | JSON 文件（知识库）、SQLite（原始数据） |

---

## 编码规范

详细内容见 `specs/coding-standards.md`，核心要点如下：

### 风格

- **PEP 8** 作为代码风格基准
- 变量/函数名：`snake_case`
- 类名：`PascalCase`
- 常量：`UPPER_SNAKE_CASE`
- Python 版本 **>=3.12**，格式化用 **black==24.4.0**
- TypeScript 用 **prettier**，严格模式 `strict: true` + `noUncheckedIndexedAccess: true`

### 文档

- 所有模块、类、公有函数使用 **Google 风格 docstring**
- 示例：

```python
def fetch_trending_repos(limit: int = 20) -> list[dict]:
    """获取 GitHub Trending 仓库列表。

    Args:
        limit: 返回的仓库数量上限，默认 20。

    Returns:
        包含仓库信息的字典列表，每项含 name, url, description, stars。

    Raises:
        NetworkError: 网络请求失败时抛出。
    """
    pass
```

### 类型检查

- Python 用 `mypy --strict`
- 禁止硬编码业务常量，字面值抽成 `constants.py` 或枚举

### 异常处理

- 自定义异常继承 `BaseAppError`
- 禁止裸 `except`

### 日志与输出

- **禁止裸 `print()`**，统一使用 `log` 模块，`print()` 仅限 `__main__`

```python
from utils.log import log

log.info("任务完成，共处理 %d 条记录", count)
log.warning("跳过重复条目: %s", url)
```

### 依赖与 Import

- 依赖用 `pyproject.toml`
- import 用 `isort` 统一顺序

### Git Commit

- 用 **Conventional Commits** 格式

### CI 验证

```bash
ruff check . && ruff format --check . && mypy . && pytest --cov --cov-fail-under=80
check-jsonschema knowledge/**/*.json
```

| 层级 | 覆盖率要求 |
|------|-----------|
| 业务逻辑层 | >= 90% |
| 工具层 | >= 80% |
| 边界适配层 | >= 50% |

---

## 项目结构

```
.
├── workflows/                  # LangGraph 工作流实现
│   ├── __init__.py
│   ├── state.py               # KBState 定义（TypedDict）
│   ├── graph.py                # 工作流图定义与入口
│   ├── planner.py              # 策略节点（plan_strategy / planner_node）
│   ├── collector.py            # 采集节点（collect_node）
│   ├── analyzer.py             # 分析节点（analyze_node）
│   ├── reviewer.py             # 审核节点（review_node）
│   ├── reviser.py             # 修订节点（revise_node）
│   ├── organizer.py            # 整理保存节点（organize_node）
│   ├── human_flag.py           # 人工介入节点（human_flag_node）
│   └── model_client.py         # LLM 调用封装（chat_json / JSONTruncatedError）
├── knowledge/
│   ├── raw/                   # 原始抓取数据（JSON，按日期分区）
│   │   └── 2026-05-05/
│   │       └── raw.json
│   ├── articles/              # AI 分析后的结构化知识条目
│   │   └── {id}.json
│   └── pending_review/         # 待人工审核的条目（human_flag 兜底）
├── mcp_knowledge_server.py    # Local MCP tool
├── main.py                    # 入口脚本
└── AGENTS.md
```

---

## 工作流节点

```
plan → collect → analyze → review ─┬─→ organize（整理保存）→ END
                                   ├─→ revise（iter < max） → review（循环）
                                   └─→ human_flag（iter >= max）→ END
```

| 节点 | 文件 | 职责 |
|------|------|------|
| **Planner** | `planner.py` | 根据 `target_count` 生成采集策略（lite/standard/full），输出 `plan` |
| **Collector** | `collector.py` | 采集 GitHub 仓库，写入 `knowledge/raw/` |
| **Analyzer** | `analyzer.py` | LLM 生成摘要、技术栈、标签、评分，写入 `analyses` |
| **Reviewer** | `reviewer.py` | 五维度评分，`weighted_score >= 7.0` 通过 |
| **Reviser** | `reviser.py` | 根据 `review_feedback` 修正 `analyses` |
| **Organizer** | `organizer.py` | 过滤、去重、写入 `knowledge/articles/` |
| **HumanFlag** | `human_flag.py` | 达最大迭代后兜底，写入 `pending_review/` |

---

## 知识条目 JSON 格式

```json
{
  "id": "uuid-v4",
  "title": "项目名称 / 文章标题",
  "source": "github_trending | hacker_news",
  "source_url": "https://...",
  "summary": "AI 生成的一句话描述",
  "tech_stack": ["Python", "LangChain", "OpenAI"],
  "problem_solved": "解决什么问题",
  "why_valuable": "为什么有价值",
  "tags": ["AI", "Agent", "开源"],
  "status": "raw | analyzed | published | archived",
  "created_at": "2026-05-05T10:30:00Z",
  "updated_at": "2026-05-05T10:30:00Z",
  "published_to": []
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | UUID v4，唯一标识 |
| `title` | string | 项目/文章标题 |
| `source` | enum | 数据来源 |
| `source_url` | string | 原始链接 |
| `summary` | string | AI 生成摘要 |
| `tech_stack` | string[] | 技术栈数组 |
| `problem_solved` | string | 解决的问题 |
| `why_valuable` | string | 价值描述 |
| `tags` | string[] | 标签（用于分类过滤） |
| `status` | enum | 当前状态 |
| `created_at` | ISO8601 | 创建时间 |
| `updated_at` | ISO8601 | 更新时间 |
| `published_to` | string[] | 已分发的渠道 |

---

## KBState 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `sources` | list[dict] | 采集阶段输出的原始条目列表 |
| `analyses` | list[dict] | LLM 逐条分析后的结构化结果 |
| `articles` | list[dict] | 经过质量审核、去重后的最终知识条目 |
| `plan` | dict | Planner 输出的策略参数（tier/per_source_limit/relevance_threshold/max_iterations） |
| `review_feedback` | str | 审核节点对当前 analyses 的反馈意见 |
| `review_passed` | bool | 当前 analyses 是否通过审核 |
| `iteration` | int | 当前审核循环的轮次，初始 0 |
| `cost_tracker` | dict | LLM token 消耗汇总 |
| `needs_human_review` | bool | 是否需要人工介入 |

---

## 三档策略（Planner）

| 档位 | 触发条件 | per_source_limit | relevance_threshold | max_iterations |
|------|---------|-----------------|-------------------|----------------|
| **lite** | target < 10 | 5 | 0.7 | 1 |
| **standard** | 10 <= target < 20 | 10 | 0.5 | 2 |
| **full** | target >= 20 | 20 | 0.4 | 3 |

- `target_count` 默认从环境变量 `PLANNER_TARGET_COUNT` 读取（默认 10）
- 每个策略 dict 含 `rationale` 字段说明选型理由

---

## Agent 角色概览

| 角色 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **Collector** | 采集 GitHub Trending / HN 最新动态，过滤 AI/LLM/Agent 相关条目 | 数据源 URL | 原始条目列表（sources） |
| **Analyzer** | AI 分析条目内容，生成摘要、技术栈、标签、评分 | sources | analyses（结构化分析结果） |
| **Reviewer** | 五维度评分，计算加权总分，判断是否通过审核 | analyses | review_passed / review_feedback |
| **Reviser** | 根据审核反馈修正 analyses | analyses + review_feedback | 改进后的 analyses |
| **Organizer** | 过滤、去重、写入 `knowledge/articles/` | analyses | saved_ids |
| **HumanFlag** | 达最大迭代后兜底保存到 `pending_review/` | analyses + iteration | needs_human_review=True |

### 工作流

```
[GitHub Trending / HN]
        │
        ▼
   ┌──────────┐
   │ Collector │──▶ knowledge/raw/
   └──────────┘
        │
        ▼
   ┌──────────┐
   │ Analyzer  │──▶ 生成 summary / tech_stack / tags
   └──────────┘
        │
        ▼
   ┌──────────┐
   │ Reviewer  │──▶ review_passed=True? ─┐
   └──────────┘                        │
        │ (False)                       │
        ▼                               │
   ┌──────────┐                        │
   │ Reviser  │──▶ 再审                │
   └──────────┘                        │
        │                               ▼
        │                        ┌───────────┐
        └───────────────────────▶│ Organizer │──▶ 知识库（articles/{id}.json）
                                 └───────────┘
                                      │
                                      ▼
                              多渠道分发（Telegram / 飞书）
```

---

## 红线（绝对禁止）

以下操作无论任何情况均不可执行：

| 红线 | 说明 |
|------|------|
| **删除知识库文件** | 不得删除 `knowledge/` 目录下任何历史数据 |
| **硬编码凭证** | API Token、密钥等必须通过环境变量注入，禁止写入代码 |
| **修改历史条目** | `status=published` 的条目不可修改，只能新增或标记 `archived` |
| **直接推送到生产** | 任何分发操作必须经过 `status=published` 审核 |
| **爬取私有内容** | 仅限公开数据源，不碰 GitHub 私有仓库等 |
| **日志泄露敏感信息** | 禁止在日志中打印 URL 参数、Token 等敏感数据 |

---

## 调试命令

```bash
# 本地单次运行（默认 target=10）
PLANNER_TARGET_COUNT=5 python -m workflows.graph

# 开启 LLM 调用 debug 日志
DEBUG_LLM_CALLS=true python -m workflows.graph

# 验证 JSON 输出
python -c "import json, glob; [json.load(open(f)) for f in glob('knowledge/articles/*.json')]"
```