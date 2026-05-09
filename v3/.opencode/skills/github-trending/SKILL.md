---
name: github-trending
description: 当需要采集 GitHub 热门开源项目时使用此技能
allowed-tools:
  - Read
  - Grep
  - Glob
  - WebFetch
---

# GitHub Trending 采集技能

## 使用场景

当需要采集 GitHub Trending 页面中的 AI/LLM/Agent 相关热门开源项目时使用此技能。

## 执行步骤

### Step 1: 搜索热门仓库
调用 GitHub Search API 获取当前热门仓库列表：

```
GET https://api.github.com/search/repositories?q=stars:>1000+pushed:>2024-01-01&sort=stars&order=desc&per_page=100
```

### Step 2: 提取关键信息
从返回结果中提取每条仓库的：name, full_name, html_url, description, stargazers_count, language, topics

### Step 3: 过滤筛选
**纳入条件**（满足任一）：
- topics 或 description 中包含 AI/LLM/Agent 相关关键词
- 仓库属于 awesome-{ai,llm,agent} 类列表（非直接排除，而是降低优先级）

**排除条件**：
- topics 包含 "awesome-list"
- description 为空或过于简单
- 非英语主导的项目

### Step 4: 去重检查
读取 `knowledge/raw/` 目录中最近 7 天的历史数据，检查是否存在完全相同的仓库（按 full_name 匹配），已存在的条目跳过。

### Step 5: 撰写中文摘要
对每个通过筛选的仓库撰写中文摘要，遵循公式：

> **项目名** + 做什么 + **为什么值得关注**

示例：
> **AutoGLM**：智谱AI开源的浏览器自动化Agent，能够根据自然语言指令完成网页搜索、内容提取、表单填写等任务，相比传统爬虫方案更灵活且支持复杂交互逻辑。

### Step 6: 排序取 Top15
按 stars 数量降序排列，选取前 15 条高质量条目。

### Step 7: 输出 JSON 文件
将结果写入 `knowledge/raw/github-trending-YYYY-MM-DD.json`，使用今日实际日期。

## 注意事项

- GitHub API 有速率限制（60请求/小时），批量采集时需添加适当延迟
- 历史数据保留 30 天，超期数据可归档但不可删除
- 所有 stars 数量以 API 返回的 `stargazers_count` 为准
- 若仓库无 description，尝试从 README 首行补充

## 输出格式

```json
{
  "source": "github_trending",
  "skill": "github-trending",
  "collected_at": "2026-05-05T10:30:00Z",
  "items": [
    {
      "name": "AutoGLM",
      "url": "https://github.com/THUDM/AutoGLM",
      "summary": "智谱AI开源的浏览器自动化Agent...",
      "stars": 12500,
      "language": "Python",
      "topics": ["agent", "browser-automation", "llm"]
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `source` | string | 数据来源固定值 |
| `skill` | string | 调用的技能名称 |
| `collected_at` | ISO8601 | 采集时间 |
| `items` | array | 仓库条目数组 |
| `items[].name` | string | 仓库名 |
| `items[].url` | string | 仓库主页 URL |
| `items[].summary` | string | 中文摘要 |
| `items[].stars` | integer | 星标数 |
| `items[].language` | string | 主要语言 |
| `items[].topics` | string[] | 主题标签 |