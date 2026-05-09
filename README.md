# AI Knowledge Base

自动从 GitHub Trending 和 Hacker News 采集 AI/LLM/Agent 领域的技术动态，经 AI 分析后结构化存储，支持搜索、订阅与多渠道分发。

---

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Sources                              │
│            GitHub Trending    ·    Hacker News                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LangGraph Pipeline (v4)                        │
│                                                                  │
│   plan ──▶ collect ──▶ analyze ──▶ review ──┬──▶ organize ──▶ END │
│                                             ├──▶ revise ──▶ review (loop)  │
│                                             └──▶ human_flag ──▶ END       │
└────────────────────────┬─────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
   knowledge/raw/               knowledge/articles/
   (原始数据)                    (结构化知识条目)
          │                             │
          └──────────────┬──────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     KnowledgeBot (v4)                            │
│   搜索 · 今日速递 · 热榜排行 · 订阅管理 · 权限控制                │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
               多渠道分发 (Telegram / 飞书)
```

### 节点职责

| 节点 | 职责 |
|------|------|
| **Planner** | 根据 target_count 生成采集策略（lite/standard/full） |
| **Collector** | 采集 GitHub 仓库，写入 `knowledge/raw/` |
| **Analyzer** | LLM 生成摘要、技术栈、标签、评分 |
| **Reviewer** | 五维度评分，weighted_score >= 7.0 通过 |
| **Reviser** | 根据审核反馈修正分析结果 |
| **Organizer** | 过滤、去重、写入 `knowledge/articles/` |
| **HumanFlag** | 达最大迭代后兜底保存到 `pending_review/` |

### 三档策略

| 档位 | 触发条件 | per_source_limit | relevance_threshold | max_iterations |
|------|---------|-----------------|-------------------|----------------|
| **lite** | target < 10 | 5 | 0.7 | 1 |
| **standard** | 10 <= target < 20 | 10 | 0.5 | 2 |
| **full** | target >= 20 | 20 | 0.4 | 3 |

---

## 快速开始

### 前置依赖

- Python >= 3.12

### 安装

```bash
# 进入 v4-production 版本
cd v4-production

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

```bash
export LLM_PROVIDER=deepseek       # 或 qwen / minimax
export DEEPSEEK_API_KEY=your_key
export QWEN_API_KEY=your_key
export MINIMAX_API_KEY=your_key
```

### 运行采集

```bash
# 默认 target=10
PLANNER_TARGET_COUNT=5 python -m workflows.graph

# 开启 LLM debug 日志
DEBUG_LLM_CALLS=true python -m workflows.graph
```

### 验证输出

```bash
python -c "import json, glob; [json.load(open(f)) for f in glob('knowledge/articles/*.json')]"
```

### 知识库查询

```python
from bot.knowledge_bot import KnowledgeBot, Intent

bot = KnowledgeBot()

# 搜索
bot.handle_message("user1", "/search AI Agent")

# 今日速递
bot.handle_message("user1", "/today")

# 热榜
bot.handle_message("user1", "/top 10")
```

---

## 项目结构

```
.
├── v1/                           # v1: 早期版本（OpenCode agents）
├── v2/                           # v2: pipeline 架构
├── v3/                           # v3: LangGraph 工作流
├── v4-production/                # v4: 生产级实现（当前主力版本）
│   ├── workflows/                # LangGraph 节点实现
│   │   ├── state.py              # KBState 定义
│   │   ├── graph.py              # 工作流入口
│   │   ├── planner.py            # 策略节点
│   │   ├── collector.py           # 采集节点
│   │   ├── analyzer.py           # 分析节点
│   │   ├── reviewer.py           # 审核节点
│   │   ├── reviser.py            # 修订节点
│   │   ├── organizer.py          # 整理节点
│   │   ├── human_flag.py         # 人工兜底节点
│   │   └── model_client.py       # LLM 调用封装
│   ├── bot/
│   │   └── knowledge_bot.py      # 知识库机器人（搜索/订阅/权限）
│   └── knowledge/
│       ├── raw/                   # 原始采集数据
│       ├── articles/              # 结构化知识条目
│       └── pending_review/         # 待人工审核
├── .github/workflows/
│   └── daily-collect.yml         # 每日定时采集 CI
└── notes/                        # 开发笔记
```

---

## 知识条目格式

```json
{
  "id": "uuid-v4",
  "title": "项目名称",
  "source": "github_trending | hacker_news",
  "source_url": "https://...",
  "summary": "AI 生成的一句话描述",
  "tech_stack": ["Python", "LangChain"],
  "problem_solved": "解决什么问题",
  "why_valuable": "为什么有价值",
  "tags": ["AI", "Agent", "开源"],
  "status": "raw | analyzed | published | archived",
  "created_at": "2026-05-05T10:30:00Z",
  "updated_at": "2026-05-05T10:30:00Z",
  "published_to": []
}
```

---

## License

Apache 2.0
