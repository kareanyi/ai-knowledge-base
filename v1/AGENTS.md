# AI 知识库助手 - AGENTS.md

## 项目概述

AI 知识库助手自动从 GitHub Trending 和 Hacker News 采集 AI/LLM/Agent 领域的技术动态，经 AI 分析后结构化存储为 JSON 格式的知识条目，并支持多渠道分发（ Telegram/飞书）。

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
├── .opencode/
│   ├── agents/              # Agent 定义（LangGraph 节点）
│   │   ├── collector.py     # 采集 Agent
│   │   ├── analyzer.py      # 分析 Agent
│   │   └── organizer.py     # 整理 Agent
│   └── skills/              # Skill 定义（原子能力封装）
│       ├── github_fetch.md
│       ├── hn_fetch.md
│       └── notify.md
├── knowledge/
│   ├── raw/                 # 原始抓取数据（JSON，按日期分区）
│   │   └── 2026-05-05/
│   └── articles/            # AI 分析后的结构化知识条目
│       └── entries.json
├── utils/
│   ├── log.py               # 日志封装
│   └── dedup.py             # 去重工具
├── main.py                  # 入口脚本
├── requirements.txt
└── AGENTS.md                # Agent 定义与规范
```

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

## Agent 角色概览

| 角色 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **Collector** | 采集 GitHub Trending / HN 最新动态，过滤 AI/LLM/Agent 相关条目 | 数据源 URL | 原始条目列表（raw） |
| **Analyzer** | AI 分析条目内容，生成摘要、技术栈、标签等结构化信息 | 原始条目 | 分析后的知识条目（analyzed） |
| **Organizer** | 去重检查、质量审核、打标签、决定分发渠道 | 分析后条目 | 可发布条目（published） |

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
   ┌───────────┐
   │ Organizer │──▶ 知识库（articles/entries.json）
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
# 本地单次运行
python main.py

# 验证 JSON 输出
python -c "import json; json.load(open('knowledge/articles/entries.json'))"

# 查看采集日志
python main.py --log-level DEBUG
```
