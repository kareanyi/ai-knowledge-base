# Organizer Agent 完整链路

## Parent

specs/agents-prd.md

## What to build

实现 Organizer Agent：读取 analyzed 文章，去重审核，标记 published。

## Acceptance criteria

- [ ] 读取 `knowledge/articles/*.json`（status=analyzed）
- [ ] 基于 source_url 去重
- [ ] 质量审核后修改 status=published
- [ ] 生成状态文件 `knowledge/status/{run_id}/organizer.json`
- [ ] 检查上游 analyzer 状态，已 completed 则跳过

## Schema

- 输入/输出：`specs/schemas/article.json`
- 状态：`specs/schemas/agent-status.json`

## Blocked by

- #002 Analyzer Agent 完整链路