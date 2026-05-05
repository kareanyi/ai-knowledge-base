---
name: tech-summary
description: 当需要对采集的技术内容进行深度分析总结时使用此技能
allowed-tools:
  - Read
  - Grep
  - Glob
  - WebFetch
---

# Tech Summary 深度分析技能

## 使用场景

当需要对 GitHub Trending 或其他来源采集的技术内容进行结构化深度分析、提取洞察时使用此技能。

## 执行步骤

### Step 1: 读取原始数据
扫描 `knowledge/raw/` 目录，读取最近一次采集的 JSON 文件（如 `github-trending-YYYY-MM-DD.json`）。

### Step 2: 逐条深度分析
对每条项目进行结构化分析，包含以下维度：

| 分析维度 | 说明 |
|----------|------|
| **摘要** | 不超过 50 字，清晰表达本质 |
| **技术亮点** | 列举 2-3 个，用事实说话，忌空洞形容 |
| **评分** | 1-10 分，附评分理由 |
| **标签建议** | 3-5 个垂直领域标签 |

评分标准参考：

| 分数段 | 含义 |
|--------|------|
| 9-10 分 | 改变格局：突破性创新或重大技术突破 |
| 7-8 分 | 直接有帮助：解决实际问题，落地性强 |
| 5-6 分 | 值得了解：有一定价值，可保持关注 |
| 1-4 分 | 可略过：同质化严重或质量一般 |

### Step 3: 趋势发现
分析所有条目，提取：
- **共同主题**：出现频率高的技术方向或解决的问题
- **新概念**：近期出现频率上升的概念或技术范式
- **值得关注的变化**：与上一期相比的差异点

### Step 4: 输出分析结果
将完整分析结果写入 `knowledge/articles/summary-YYYY-MM-DD.json`。

## 注意事项

- 每条项目的摘要必须控制在 50 字以内，言简意赅
- 技术亮点需用具体事实支撑，避免"很强"、"很先进"等空洞描述
- 评分时保持一致性，相同量级的项目评分应相近
- 趋势发现应基于数据，而非主观臆测

## 约束条件

**评分分布约束**：单个分析批次中（最多 15 个项目），9-10 分的项目不得超过 2 个。

**目的**：避免评分标准过于宽松，确保真正顶尖的项目能脱颖而出。

## 输出格式

```json
{
  "summary_date": "2026-05-05",
  "source_file": "github-trending-2026-05-05.json",
  "item_count": 15,
  "items": [
    {
      "name": "AutoGLM",
      "url": "https://github.com/THUDM/AutoGLM",
      "summary": "智谱AI开源的浏览器自动化Agent，支持自然语言指令完成复杂网页操作。",
      "tech_highlights": [
        "基于 Claude 3.5 的视觉理解能力，支持动态网页渲染",
        "创新性提出「意图链」架构，将复杂任务拆解为可执行步骤",
        "开源 2 周斩获 12k Star，生态发展迅速"
      ],
      "score": 8,
      "score_reason": "浏览器自动化能力扎实，落地场景清晰，开源策略明智。",
      "tags": ["agent", "browser-automation", "llm"]
    }
  ],
  "trends": {
    "common_themes": ["Agent", "RAG", "多模态"],
    "new_concepts": ["Small Language Model", "Local LLM"],
    "notable_changes": ["开源模型权重成趋势"]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `summary_date` | string | 分析日期 |
| `source_file` | string | 原始数据来源 |
| `item_count` | integer | 分析项目总数 |
| `items` | array | 分析结果数组 |
| `items[].name` | string | 项目名 |
| `items[].url` | string | 项目 URL |
| `items[].summary` | string | 50 字以内摘要 |
| `items[].tech_highlights` | string[] | 2-3 条技术亮点 |
| `items[].score` | integer | 1-10 评分 |
| `items[].score_reason` | string | 评分理由 |
| `items[].tags` | string[] | 标签数组 |
| `trends` | object | 趋势发现 |
| `trends.common_themes` | string[] | 共同主题 |
| `trends.new_concepts` | string[] | 新概念 |
| `trends.notable_changes` | string[] | 显著变化 |