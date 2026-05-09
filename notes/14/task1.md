## 检查

```shell
root@VM-0-3-ubuntu:~/ai-knowledge-base/v4-production# python3 -c "
import json
d = json.load(open('knowledge/articles/index.json'))
print(f'索引共 {len(d)} 条')
print('样例:', d[0])
"
索引共 160 条
样例: {'id': '2026-04-11-000', 'title': 'langgenius/dify', 'category': 'framework', 'relevance_score': 0.9}
root@VM-0-3-ubuntu:~/ai-knowledge-base/v4-production# ls knowledge/articles/2026-04-11-000.json
python3 -c "
import json
a = json.load(open('knowledge/articles/2026-04-11-000.json'))
print('字段:', list(a.keys()))
"
knowledge/articles/2026-04-11-000.json
字段: ['id', 'title', 'source', 'url', 'collected_at', 'summary', 'tags', 'relevance_score', 'category', 'key_insight']
root@VM-0-3-ubuntu:~/ai-knowledge-base/v4-production# 
```

## 验证formatter

```shell
millerlin@192 v4-production % uv run python3 -c "
import json
from distribution.formatter import json_to_markdown, json_to_telegram, json_to_feishu, json_to_wechat_clawbot

article = json.load(open('knowledge/articles/2026-04-11-000.json'))

print('=== Markdown ===')
print(json_to_markdown(article))
print()
print('=== Telegram ===')
print(json_to_telegram(article))
print()
print('=== Feishu (前 200 字符) ===')
print(json.dumps(json_to_feishu(article), ensure_ascii=False)[:200])
print()
print('=== wechat ===')
print(json_to_wechat_clawbot(article))
"
=== Markdown ===
## langgenius/dify

**来源**: github | **日期**: 2026-04-11 | **相关性**: 🟢 0.9

**标签**: LLM应用开发 / 智能体工作流 / 低代码平台 / RAG / 开源

Dify 是一个开源的 LLM 应用开发平台，旨在让开发者能够快速构建和部署基于大语言模型的智能体工作流和应用程序。它提供了直观的可视化界面，支持编排包含多种工具、知识库和复杂逻辑的 AI 工作流，并集成了模型管理、提示工程、RAG（检索增强生成）和 Agent 能力。其核心优势在于将开发、测试、部署和运维流程一体化，降低了从原型到生产环境的门槛，适用于构建聊天机器人、智能助手、内容生成等多种 AI 应用场景。

🔗 原文: https://github.com/langgenius/dify

=== Telegram ===
*langgenius/dify*
📊 🟢 0.9 | 📂 github
🏷️ LLM应用开发 智能体工作流 低代码平台 RAG 开源

Dify 是一个开源的 LLM 应用开发平台，旨在让开发者能够快速构建和部署基于大语言模型的智能体工作流和应用程序。它提供了直观的可视化界面，支持编排包含多种工具、知识库和复杂逻辑的 AI 工作流，并集成了模型管理、提示工程、RAG（检索增强生成）和 Agent 能力。其核心优势在于将开发、测试、部署和运维流程一体化，降低了从原型到生产环境的门槛，适用于构建聊天机器人、智能助手、内容生成等多种 AI 应用场景。

🔗 https://github.com/langgenius/dify

=== Feishu (前 200 字符) ===
{"msg_type": "interactive", "card": {"header": {"title": {"tag": "plain_text", "content": "langgenius/dify"}, "template": "#00A381"}, "elements": [{"tag": "div", "text": {"tag": "lark_md", "content":

=== wechat ===
🟢 langgenius/dify (0.9) | [LLM应用开发 智能体工作流 低代码平台 RAG 开源] | Dify 是一个开源的 LLM 应用开发平台，旨在让开发者能够快速构建和部署基于大语言模型的智能体工作流和应用程序。它提供了直观的可视化界面，支持编排包含多种工具、知识库和复杂逻辑的 AI 工作流，并... | https://github.com/langgenius/dify
millerlin@192 v4-production %
```

```shell
millerlin@192 v4-production % uv run python3 -c "
from distribution.formatter import generate_daily_digest
result = generate_daily_digest(date='2026-04-11', top_n=5)
print('=== Markdown 简报 ===')
print(result['markdown'])
"
=== Markdown 简报 ===
# 📚 2026-04-11 知识简报（共 5 条）
## langchain-ai/langchain

**来源**: github | **日期**: 2026-04-11 | **相关性**: 🟢 0.9

**标签**: llm-framework / agent / rag / python / open-source

LangChain是一个用于构建基于大型语言模型（LLM）应用程序的开源框架。它提供了一套工具和组件，使开发者能够轻松地将LLM与外部数据源、计算资源和工具连接起来，从而创建功能强大的智能代理（Agent）和检索增强生成（RAG）应用。其核心价值在于简化了复杂LLM应用的开发流程，通过模块化设计支持链式调用、记忆管理、工具集成等功能，是当前AI应用开发领域的重要基础设施之一。

🔗 原文: https://github.com/langchain-ai/langchain
---
## bytedance/deer-flow

**来源**: github | **日期**: 2026-04-11 | **相关性**: 🟢 0.9

**标签**: 智能体框架 / 长期任务规划 / 开源项目 / 字节跳动 / 多智能体协作

Deer-Flow 是字节跳动开源的长期任务智能体框架，专注于处理需要数分钟到数小时完成的复杂任务。该框架通过沙箱环境、记忆系统、工具调用、技能库、子智能体协作和消息网关等核心模块，实现了对多步骤任务的规划、执行与监控。它支持研究、编码和创作等高级认知任务，为构建具备长期规划和执行能力的AI智能体提供了系统化解决方案。

🔗 原文: https://github.com/bytedance/deer-flow
---
## hiyouga/LlamaFactory

**来源**: github | **日期**: 2026-04-11 | **相关性**: 🟢 0.9

**标签**: 大语言模型 / 微调框架 / 高效训练

LlamaFactory是一个统一的、高效的微调框架，支持100多种大型语言模型和视觉语言模型。该项目在ACL 2024上发表，旨在简化大模型的微调流程，提供统一的接口和高效的训练策略，降低研究人员和开发者的使用门槛。它集成了多种主流微调方法，如LoRA、QLoRA等，并支持分布式训练，显著提升了微调效率和模型性能。

🔗 原文: https://github.com/hiyouga/LlamaFactory
---
## infiniflow/ragflow

**来源**: github | **日期**: 2026-04-11 | **相关性**: 🟢 0.9

**标签**: rag / agent / llm / open-source / knowledge-base

RAGFlow 是一个领先的开源检索增强生成（RAG）引擎，它将前沿的 RAG 技术与智能体（Agent）能力深度融合，旨在为大型语言模型（LLM）构建一个卓越的上下文层。该项目通过结合深度文档解析、智能检索和可配置的生成流程，显著提升了基于文档的问答、知识库构建等应用的准确性和可靠性。其开源特性允许开发者灵活定制和集成，是构建企业级知识智能应用的有力工具。

🔗 原文: https://github.com/infiniflow/ragflow
---
## langgenius/dify

**来源**: github | **日期**: 2026-04-11 | **相关性**: 🟢 0.9

**标签**: LLM应用开发 / 智能体工作流 / 低代码平台 / RAG / 开源

Dify 是一个开源的 LLM 应用开发平台，旨在让开发者能够快速构建和部署基于大语言模型的智能体工作流和应用程序。它提供了直观的可视化界面，支持编排包含多种工具、知识库和复杂逻辑的 AI 工作流，并集成了模型管理、提示工程、RAG（检索增强生成）和 Agent 能力。其核心优势在于将开发、测试、部署和运维流程一体化，降低了从原型到生产环境的门槛，适用于构建聊天机器人、智能助手、内容生成等多种 AI 应用场景。

🔗 原文: https://github.com/langgenius/dify
---
millerlin@192 v4-production %
```