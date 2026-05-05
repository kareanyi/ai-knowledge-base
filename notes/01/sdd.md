# AGENTS.md

## 项目概述
AI 知识库：每天抓取 GitHub Trending AI 项目，Agent 分析后输出结构化知识条目，沉淀为可检索的知识库。

---

## 技术栈
- 语言：Python
- 主要依赖：requests, BeautifulSoup / Playwright（页面抓取）, OpenAI GPT（Agent 分析）, json

---

## 目录结构
```
.
├── agents/              # Agent 相关代码
│   └── analyzer.py      # 内容分析 Agent
├── scrapers/            # 抓取模块
│   └── github_trending.py
├── knowledge_base/      # 知识库存储（JSON 文件）
│   └── entries.json
├── specs/              # 项目规格文档
├── AGENTS.md            # 本文件
└── main.py              # 入口脚本
```

---

## 工作流程

### 1. 抓取 GitHub Trending
- 访问 GitHub Trending 页面
- 过滤条件：repo topics 包含 `ai`、`llm`、`agent`（三选一即收录）
- 数量上限：前 20 条
- 输出：未处理的原始项目列表（含 name, url, description）

### 2. Agent 内容分析
- 对每个项目调用 Agent
- 分析维度：
    - 项目一句话描述
    - 技术栈（从 README / topics 提取）
    - 解决什么问题
    - 为什么有价值
- 语言：中文输出（覆盖英文 + 中文项目）

### 3. 构建知识条目
严格按以下字段输出 JSON：
```json
{
  "name": "项目名",
  "description": "一句话描述",
  "trending_date": "上榜日期（YYYY-MM-DD）",
  "github_url": "链接",
  "tech_stack": ["技术栈数组"],
  "problem_solved": "解决什么问题",
  "why_valuable": "为什么有价值",
  "tags": ["AI", "开源"]
}
```

### 4. 去重与存储
- 写入 `knowledge_base/entries.json`
- 写入前检查 github_url 是否已存在，存在则跳过
- 每次运行追加新条目，不覆盖历史

---

## 约束清单（严格遵守）

### 不做什么
- 不做推送/通知
- 不做用户评论/互动
- 不做多语言翻译

### 边界
- 只处理公开 GitHub 仓库，不碰私有仓库
- 覆盖英文 + 中文项目（分析输出用中文）
- 知识库内去重（以 github_url 为唯一键）

---

## 验收标准
- 连续跑 3 天，每天有输出
- 知识条目 JSON 可被解析
- tags 能区分不同项目
- 可导入 Obsidian/Oursql 等笔记工具

---

## 调试命令
```bash
# 本地单次运行
python main.py

# 验证 JSON 输出
python -c "import json; json.load(open('knowledge_base/entries.json'))"
```
