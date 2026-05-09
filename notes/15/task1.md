## 测试

```shell
millerlin@192 v4-production % uv run python3 <<'PY'
from bot.knowledge_bot import KnowledgeBot, recognize_intent, Intent

# 测试意图识别
tests = [
    ('/search MCP', Intent.SEARCH, 'MCP'),
    ('/today', Intent.TODAY, ''),
    ('/top', Intent.TOP, ''),
    ('搜索 Agent 文章', Intent.SEARCH, ''),
    ('今天有什么新内容', Intent.TODAY, ''),
    ('随便聊聊', Intent.UNKNOWN, ''),
]

print('=== 意图识别测试 ===')
for text, expected_intent, _ in tests:
    intent, args = recognize_intent(text)
    status = '✅' if intent == expected_intent else '❌'
    print(f'{status} "{text}" → {intent.value} (args={args!r})')

# 测试 Bot 完整流程
bot = KnowledgeBot()
print()
print('=== Bot 消息处理测试 ===')
for text in ['/help', '/search Agent', '/today', '搜索 MCP 协议']:
    print(f'输入: {text}')
    print(f'回复: {bot.handle_message("test-user", text)[:80]}...')
    print()
PY
=== 意图识别测试 ===
✅ "/search MCP" → search (args='MCP')
✅ "/today" → today (args='')
✅ "/top" → top (args='/top')
✅ "搜索 Agent 文章" → search (args='搜索 Agent 文章')
✅ "今天有什么新内容" → today (args='今天有什么新内容')
✅ "随便聊聊" → unknown (args='随便聊聊')

=== Bot 消息处理测试 ===
输入: /help
回复: 🤖 知识库机器人命令：

/search <关键词>  — 按关键词搜索
/today            — 查看今日新条目
/top [数量]      ...

输入: /search Agent
回复: 📚 搜索结果：
1. [langchain-ai/langchain](https://github.com/langchain-ai/langchain)
 ...

输入: /today
回复: 📅 今日知识速递：
1. [langchain-ai/langchain](https://github.com/langchain-ai/langchain)...

输入: 搜索 MCP 协议
回复: 📚 搜索结果：
1. [jeecgboot/JeecgBoot](https://github.com/jeecgboot/JeecgBoot)
   Jeec...

millerlin@192 v4-production %
```

```shell
millerlin@192 v4-production % uv run python3 <<'PY'
import sys; sys.path.insert(0, '.')
from bot.knowledge_bot import KnowledgeSearchEngine, recognize_intent, format_search_results

# 1. 意图识别
print('--- 意图识别 ---')
for q in ['/search agent', '/today', '/top 3', '/help', '搜一下 RAG']:
    intent, payload = recognize_intent(q)
    print(f'  {q!r:25s} → {intent.name:18s} payload={payload!r}')

# 2. 加权搜索
print()
print('--- /search agent (top 3) ---')
engine = KnowledgeSearchEngine('knowledge/articles')
results = engine.search(keyword='agent', limit=3)
print(format_search_results(results, query='agent'))
PY
--- 意图识别 ---
  '/search agent'           → SEARCH             payload='agent'
  '/today'                  → TODAY              payload=''
  '/top 3'                  → TOP                payload='3'
  '/help'                   → HELP               payload=''
  '搜一下 RAG'                 → SEARCH             payload='搜一下 RAG'

--- /search agent (top 3) ---
📚 搜索「agent」结果：

1. [langchain-ai/langchain](https://github.com/langchain-ai/langchain)
   LangChain 是一个用于构建基于大语言模型（LLM）的智能代理（Agent）和应用程序的开源框架。它提供了模块化的组件，如模型调用、提示管理、记忆、工具集...
   #LLM #Agent #Framework

2. [langchain-ai/langchain](https://github.com/langchain-ai/langchain)
   LangChain是一个用于构建基于大语言模型（LLM）的智能代理（Agent）的工程平台。它提供了模块化的组件，如模型、提示、链、代理和内存，使开发者能够轻松...
   #LLM #Agent #Framework

3. [langchain-ai/langchain](https://github.com/langchain-ai/langchain)
   LangChain 是一个用于构建基于大语言模型（LLM）的应用程序的工程平台，专注于智能代理（Agent）的开发与编排。它提供了模块化的工具链，支持链式调用、...
   #langchain #agent #llm
millerlin@192 v4-production %
```