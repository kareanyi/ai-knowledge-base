# AI 知识库助手 · Agent 规范

## 1. 项目概述

一个 AI/LLM/Agent 领域的技术动态采集与分发系统：每日自动从 GitHub Trending 和 Hacker News 抓取相关内容，经 AI 结构化分析后以 JSON 格式存储，并支持推送至 Telegram/飞书等渠道。

---

## 2. 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.12 |
| 模型 | OpenCode + 国产大模型（DeepSeek / Qwen / GLM） |
| 编排 | LangGraph |
| 技能框架 | OpenClaw |

---

## 3. 编码规范

- **风格**：[PEP 8](https://pep8.org/)
- **命名**：snake_case（变量/函数/模块），PascalCase（类名）
- **文档**：Google 风格 docstring

```python
def fetch_trending(lang: str = "python", days: int = 1) -> list[dict]:
    """Fetch GitHub trending items.

    Args:
        lang: Programming language filter.
        days: Number of days to look back.

    Returns:
        List of trending repository dicts.
    """
    ...
```

- **日志**：统一使用 `logging`，禁止裸 `print()`
- **类型**：所有公开函数必须标注类型提示

---

## 4. 项目结构

```
.
├── .opencode/
│   ├── agents/          # Agent 定义（角色、指令）
│   └── skills/         # OpenClaw Skill 封装
├── knowledge/
│   ├── raw/            # 原始抓取内容（JSONL）
│   └── articles/       # AI 分析后的结构化条目
└── AGENTS.md
```

---

## 5. 知识条目 JSON 格式

```json
{
  "id": "gh-20250505-001",
  "title": "GPT-4: One Year of Insights and Lessons",
  "source_url": "https://github.com/some/repo",
  "source_type": "github_trending",
  "summary": "一篇总结 GPT-4 发布一年经验教训的博客文章...",
  "tags": ["LLM", "GPT-4", "教训总结"],
  "status": "analyzed",
  "created_at": "2025-05-05T08:00:00Z",
  "published_at": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 格式：`{source}-{date}-{seq}`，如 `hn-20250505-001` |
| `title` | string | 条目标题 |
| `source_url` | string | 原始链接 |
| `source_type` | string | `github_trending` / `hacker_news` |
| `summary` | string | AI 生成摘要（50-200 字） |
| `tags` | string[] | 关键词标签 |
| `status` | string | `raw` → `analyzed` → `published` |
| `created_at` | ISO8601 | 首次创建时间 |
| `published_at` | ISO8601 | 渠道分发时间，null 表示未发布 |

---

## 6. Agent 角色概览

| 角色 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **Collector** | 从 GitHub Trending / HN 抓取原始内容 | 关键词列表 | `knowledge/raw/*.jsonl` |
| **Analyzer** | 读取 raw 条目，生成 summary / tags，决策是否值得分发 | `knowledge/raw/` | `knowledge/articles/*.json` |
| **Curator** | 审核后分发至 Telegram / 飞书 | `knowledge/articles/` | 渠道消息 |

---

## 7. 红线（绝对禁止）

以下操作即使在 `auto-accept` 模式下也必须停下来询问用户：

- 删除 `knowledge/` 下的任何原始数据或分析结果
- 提交任何包含真实 API Key / Token 的文件（`.env`、配置文件等）
- 修改 `.opencode/agents/` 下的 Agent 定义文件
- 更改 `knowledge/articles/` 的 JSON Schema
- 向非用户明确指定的第三方渠道推送内容
- 在生产环境（飞书/Telegram 生产频道）进行测试推送
