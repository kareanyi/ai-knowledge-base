## local test result
```shell
millerlin@192 v2 % echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | uv run python3 mcp_knowledge_server.py
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "serverInfo": {"name": "knowledge-server", "version": "1.0.0"}, "capabilities": {"tools": {}}}}
millerlin@192 v2 % echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | uv run python3 mcp_knowledge_server.py
{"jsonrpc": "2.0", "id": 2, "result": {"tools": [["search_articles", {"description": "Search articles by keyword in title and summary", "inputSchema": {"type": "object", "properties": {"keyword": {"type": "string", "description": "Search keyword"}, "limit": {"type": "integer", "description": "Max results", "default": 5}}, "required": ["keyword"]}}], ["get_article", {"description": "Get full article by ID", "inputSchema": {"type": "object", "properties": {"article_id": {"type": "string", "description": "Article UUID"}}, "required": ["article_id"]}}], ["knowledge_stats", {"description": "Get knowledge base statistics", "inputSchema": {"type": "object", "properties": {}}}]]}}
millerlin@192 v2 % echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_articles","arguments":{"keyword":"agent","limit":3}}}' | uv run python3 mcp_knowledge_server.py
{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "[{\"id\": \"6db8cdfa-a59c-46cf-9f9f-b526a5f15a82\", \"title\": \"Google made agentic AI governance a product. Enterprises still have to catch up.\", \"source\": \"rss\", \"summary\": \"Google announced the Gemini Enterprise Agent Platform at Cloud Next '26, making agentic AI governance a native product feature built into the platform rather than an afterthought. This marks a signifi\", \"score\": 7}]"}]}}
millerlin@192 v2 % echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"knowledge_stats","arguments":{}}}' | uv run python3 mcp_knowledge_server.py
{"jsonrpc": "2.0", "id": 4, "result": {"content": [{"type": "text", "text": "{\"total_articles\": 14, \"source_distribution\": {\"hacker_news\": 5, \"github_trending\": 5, \"rss\": 4}, \"top_tags\": [{\"tag\": \"AI Governance\", \"count\": 3}, {\"tag\": \"NLP\", \"count\": 3}, {\"tag\": \"AI Safety\", \"count\": 2}, {\"tag\": \"Enterprise AI\", \"count\": 2}, {\"tag\": \"Physical AI\", \"count\": 2}, {\"tag\": \"Apple\", \"count\": 1}, {\"tag\": \"iOS\", \"count\": 1}, {\"tag\": \"Wallet\", \"count\": 1}, {\"tag\": \"PassKit\", \"count\": 1}, {\"tag\": \"Mobile\", \"count\": 1}]}"}]}}
millerlin@192 v2 %
```

## check mcp
```shell
# Check MCP servers status
$ opencode mcp list
┌  MCP Servers
│
●  ✓ knowledge connected
│      uv run python3 mcp_knowledge_server.py
│
└  1 server(s)
Thinking: Connected.
MCP 已正常工作。
```

```shell
knowledge这个mcp有哪些tools?
Thinking: The user is asking about what tools the knowledge MCP has. Looking at the available tools in the system prompt, I can see there are several knowledge-related tools:
1. knowledge_search_articles - Search articles by keyword in title and summary
2. knowledge_get_article - Get full article by ID
3. knowledge_knowledge_stats - Get knowledge base statistics
These are the three tools available for the knowledge MCP.
knowledge MCP 有 3 个 tools：
Tool	功能
knowledge_search_articles	按关键词搜索标题和摘要中的文章
knowledge_get_article	根据 ID 获取完整文章内容
knowledge_knowledge_stats	获取知识库统计信息
```

## chat with mcp
```shell
搜索知识库里关于 RAG 的文章
Thinking: The user wants to search for articles about RAG in the knowledge base.
⚙ knowledge_search_articles [keyword=RAG, limit=10]
Thinking: 搜索结果只返回了一篇关于 apache/brpc 的文章，但这并不是真正关于 RAG（Retrieval-Augmented Generation）技术的内容，只是匹配到了 "RAG" 这个字符串。用户要搜索的是 RAG 技术相关文章，需要进一步确认或重新搜索。
让我问一下用户或者再尝试搜索一下。
只找到 1 篇，是匹配到 "brpc" 中的 "RAG" 字符串。知识库中没有专门讲 RAG（检索增强生成）技术原理或实践的文章。
▣  Build · MiniMax-M2.7 · 17.1s

知识库里一共有多少篇文章？哪些标签最热门？
Thinking: The user wants to know the total number of articles in the knowledge base and the most popular tags.
⚙ knowledge_knowledge_stats 
Thinking: 用户想知道知识库有多少篇文章以及热门标签。统计结果显示：
- 共 14 篇文章
- 来源分布：hacker_news 5篇、github_trending 5篇、rss 4篇
- 最热门标签：AI Governance 和 NLP 各 3 篇，其次 AI Safety、Enterprise AI、Physical AI 各 2 篇
知识库共 14 篇文章，来源分布均匀（HN、GitHub Trending、RSS 各约 5/4 篇）。
最热门标签：AI Governance 和 NLP（各 3 篇），其次 AI Safety、Enterprise AI、Physical AI（各 2 篇）。

给我看386d4d1b-0b8e-4491-b810-28c1569c37b3这个文章详细内容
Thinking: The user wants to see the full article with ID 386d4d1b-0b8e-4491-b810-28c1569c37b3
⚙ knowledge_get_article [article_id=386d4d1b-0b8e-4491-b810-28c1569c37b3]
Thinking: Got the article details. Let me present it concisely.
graykode/nlp-tutorial | GitHub Trending
一句话描述： 面向深度学习研究者的 NLP 教程仓库，包含 Transformer、BERT、Attention 等核心模型的 PyTorch/TensorFlow 双框架实现。
技术栈： PyTorch, TensorFlow, Jupyter Notebook, Transformer, BERT
解决什么问题： 解决深度学习研究者在学习和实践 NLP 核心模型时缺乏系统性代码示例的问题。
为什么有价值： 通过简洁易懂的代码实现，帮助研究者快速理解和复现 NLP 领域的经典论文与最新模型。
标签： NLP, Deep Learning, PyTorch, TensorFlow, Transformer
状态： published | 创建于 2026-05-05
▣  Build · MiniMax-M2.7 · 13.4s

对比知识库里 agent 和 rag 相关文章的数量
Thinking: User wants to compare the number of articles about "agent" and "rag" in the knowledge base. I need to search for both keywords.
⚙ knowledge_search_articles [keyword=agent, limit=20]
⚙ knowledge_search_articles [keyword=rag, limit=20]
Thinking: Both searches returned only 1 result each, and they're not really about "agent" or "rag" specifically - just string matches. So:
- Agent 相关: 1 篇
- RAG 相关: 1 篇（实际只是匹配到 brpc）
Agent 相关： 1 篇（Google Gemini Enterprise Agent Platform）
RAG 相关： 1 篇（实际只是匹配到 apache/brpc 中的 "rag" 字符串，并非真正讲 RAG）
两者数量持平，但质量上都没有专门针对 agent 或 RAG 技术主题的文章。当前知识库主题偏 NLP/AI Governance，缺少 agent 与 RAG 方向的覆盖。
```