# Collector Agent 完整链路

## Parent

specs/agents-prd.md

## What to build

实现 Collector Agent：抓取 GitHub Trending Top 50，过滤 AI 相关，存储到 raw.json。

## Acceptance criteria

- [ ] 抓取 GitHub Trending Top 50，获取 name, url, description, stars
- [ ] 过滤 AI/LLM/Agent 相关条目（关键词匹配）
- [ ] 输出到 `knowledge/raw/{date}/raw.json`
- [ ] 生成状态文件 `knowledge/status/{run_id}/collector.json`
- [ ] 无 AI 相关条目时正常退出
- [ ] main.py 支持 `--schedule` 参数实现 UTC 0:00 每日调度

## Schema

- 输出：`specs/schemas/raw.json`
- 状态：`specs/schemas/agent-status.json`

## Blocked by

None - can start immediately