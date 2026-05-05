# AI 知识库 · 项目愿景 v1.0

## 要做什么
- 每天抓取 GitHub Trending（前 20 条，repo topics 包含 ai/llm/agent 的项目）
- 用 Agent 分析内容（项目一句话描述、技术栈、解决什么问题、为什么有价值）
- 输出结构化知识条目 JSON

## 不做什么
- 不做推送/通知
- 不做用户评论/互动
- 不做多语言翻译

## 边界
- 只处理公开 GitHub 仓库，不碰私有仓库
- 覆盖英文 + 中文项目
- 知识库内去重（同一项目不重复录入）

## 知识条目字段
```json
{
  "name": "项目名",
  "description": "一句话描述",
  "trending_date": "上榜日期",
  "github_url": "链接",
  "tech_stack": ["技术栈数组"],
  "problem_solved": "解决什么问题",
  "why_valuable": "为什么有价值",
  "tags": ["AI", "开源"]
}
```

## 验收标准
- 连续跑 3 天，每天有输出
- 知识条目 JSON 可被解析
- tags 能区分不同项目
- 可导入 Obsidian/Oursql 等笔记工具
