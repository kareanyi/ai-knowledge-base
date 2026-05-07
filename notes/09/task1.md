## 理解代码

```shell
1. 两层分类 vs 直接 LLM：关键词匹配零成本、毫秒级响应。LLM 每次调用有延迟和费用（约 10-50ms，0.1-1分钱）。实测 80%+ 的查询可以通过关键词命中，直接 LLM 兜底可以省下这部分开销。
2. 为什么是 set 而不是 dict：关键词集合只需要判断 "在不在"，用 dict 是多余的。set 的 in 查找是 O(1)，且支持 sum(1 for kw in keywords if kw in query) 这种批量计分模式。
   如果用 dict：
      # dict 的 value 无法直接用于 "是否包含" 的批量检测
   GITHUB_KEYWORDS = {"github": 1, "repo": 1}  # value 没用，还得多写
      而 set：
      github_score = sum(1 for kw in GITHUB_KEYWORDS if kw in q)  # 直接统计命中数
   
3. 兜底逻辑：
      query "search github for langchain"
           ↓
   _classify_by_keywords() → github_score=2, knowledge_score=0 → return "github_search" (命中)
   
   query "帮我看看 hermes-agent 是什么"
         ↓
   _classify_by_keywords() → 分数不够 → return None
         ↓
   _classify_by_llm() → LLM 返回 "knowledge_query" → 兜底成功
      即：关键词命中直接返回；未命中才调 LLM。
4. 新增 arxiv_search 需改 4 处：
      # 1. 新增关键词集合
   ARXIV_KEYWORDS = {"arxiv", "paper", "论文", "学术"}
   
   # 2. 新增 Intent 类型（Literal）
   Intent = Literal["github_search", "knowledge_query", "general_chat", "arxiv_search"]
   
   # 3. _classify_by_keywords 中加判断逻辑
   if arxiv_score >= 2:  # 加在 github/knowledge 之后
       return "arxiv_search"
   
   # 4. 新增 handler 函数 + 加入 INTENT_HANDLERS 字典
   def _search_arxiv(query: str) -> str:
       ...
   
   INTENT_HANDLERS = {
       "github_search": _search_github_api,
       "knowledge_query": _search_knowledge,
       "general_chat": _general_chat,
       "arxiv_search": _search_arxiv,  # 新增
   }
```

## 运行测试

```shell
millerlin@millerdeMacBook-Pro v3 % uv run python -m patterns.router "搜索最近的 AI Agent 框架"
>>> 搜索最近的 AI Agent 框架
----------------------------------------
2026-05-07 15:52:23,675 INFO Intent classified by keywords: github_search
2026-05-07 15:52:23,675 INFO Routing to github_search, query=搜索最近的 AI Agent 框架
未找到相关仓库。
millerlin@millerdeMacBook-Pro v3 % uv run python -m patterns.router "知识库里有什么关于 RAG 的内容"
>>> 知识库里有什么关于 RAG 的内容
----------------------------------------
2026-05-07 15:52:28,497 INFO Intent classified by keywords: knowledge_query
2026-05-07 15:52:28,497 INFO Routing to knowledge_query, query=知识库里有什么关于 RAG 的内容
知识库检索「知识库里有什么关于 RAG 的内容」相关条目：

- infiniflow/ragflow
  摘要：RAGFlow 是一个领先的开源检索增强生成引擎，将先进的 RAG 技术与智能体能力深度融合，为大型语言模型构建了卓越的上下文层。它通过深度文档理解、智能分块和精准检索，显著提升了 RAG 系统的准确性和可靠性。项目旨在解决传统 RAG 在文档处理、信息检索和答案生成中的痛点，提供了一个功能强大且可...
  标签：rag, agent, llm, retrieval, open-source
  来源：https://github.com/infiniflow/ragflow
millerlin@millerdeMacBook-Pro v3 % uv run python -m patterns.router "LangGraph 和 CrewAI 有什么区别"
>>> LangGraph 和 CrewAI 有什么区别
----------------------------------------
2026-05-07 15:52:36,672 INFO Intent fallback to LLM classification
2026-05-07 15:52:40,638 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-07 15:52:40,643 INFO Routing to knowledge_query, query=LangGraph 和 CrewAI 有什么区别
知识库中未找到相关内容。
millerlin@millerdeMacBook-Pro v3 %
```