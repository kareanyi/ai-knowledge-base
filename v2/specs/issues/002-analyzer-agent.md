# Analyzer Agent 完整链路

## Parent

specs/agents-prd.md

## What to build

实现 Analyzer Agent：读取 raw 数据，为每条打标签，生成 article 文件。

## Acceptance criteria

- [ ] 读取 `knowledge/raw/{date}/raw.json`
- [ ] 对每条生成 summary / tech_stack / problem_solved / why_valuable / tags
- [ ] 输出到 `knowledge/articles/{id}.json`，status=analyzed
- [ ] 生成状态文件 `knowledge/status/{run_id}/analyzer.json`
- [ ] 检查上游 collector 状态，已 completed 则跳过

## Schema

- 输入：`knowledge/raw/{date}/raw.json`
- 输出：`specs/schemas/article.json`

## Blocked by

- #001 Collector Agent 完整链路