## log

```shell
millerlin@192 v2 % uv run python3 pipeline/pipeline.py  --limit 1
2026-05-06 23:40:39,649 INFO __main__ ============================================================
2026-05-06 23:40:39,649 INFO __main__ Pipeline started: sources=['github', 'rss'] limit=1 dry_run=False
2026-05-06 23:40:39,649 INFO __main__ ============================================================
2026-05-06 23:40:39,772 INFO __main__ Loaded 50 existing URLs for deduplication
2026-05-06 23:40:39,772 INFO __main__ Collecting GitHub repositories: https://api.github.com/search/repositories
2026-05-06 23:40:40,668 INFO httpx HTTP Request: GET https://api.github.com/search/repositories?q=AI+OR+artificial+intelligence+OR+LLM+OR+large+language+model+OR+GPT+OR+machine+learning&sort=stars&order=desc&per_page=1 "HTTP/1.1 200 OK"
2026-05-06 23:40:40,744 INFO __main__ Collected 1 GitHub repositories
2026-05-06 23:40:40,744 INFO __main__ Collecting RSS feed: https://hnrss.org/frontpage
2026-05-06 23:40:42,796 INFO httpx HTTP Request: GET https://hnrss.org/frontpage "HTTP/1.1 200 OK"
2026-05-06 23:40:42,797 INFO __main__ Collected 1 items from https://hnrss.org/frontpage
2026-05-06 23:40:42,797 INFO __main__ Collecting RSS feed: https://feeds.feedburner.com/oreilly radar
2026-05-06 23:40:44,335 INFO httpx HTTP Request: GET https://feeds.feedburner.com/oreilly%20radar "HTTP/1.1 404 Not Found"
2026-05-06 23:40:44,339 WARNING __main__ RSS feed request failed for https://feeds.feedburner.com/oreilly radar: Client error '404 Not Found' for url 'https://feeds.feedburner.com/oreilly%20radar'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-05-06 23:40:44,339 INFO __main__ Collecting RSS feed: https://www.artificialintelligence-news.com/feed/
2026-05-06 23:40:45,802 INFO httpx HTTP Request: GET https://www.artificialintelligence-news.com/feed/ "HTTP/1.1 200 OK"
2026-05-06 23:40:46,104 INFO __main__ Collected 1 items from https://www.artificialintelligence-news.com/feed/
2026-05-06 23:40:46,104 INFO __main__ Collected 2 items from RSS feeds
2026-05-06 23:40:46,111 INFO __main__ Raw data saved to: /Users/millerlin/Codes/local/opencode-workspace/action-camp/ai-knowledge-base/v2/knowledge/raw/2026-05-06-raw.json
2026-05-06 23:40:46,112 INFO __main__ Analyzing [1/3]: fighting41love/funNLP
2026-05-06 23:41:02,314 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-06 23:41:02,322 INFO __main__   Score: 9, Tags: ['NLP', 'Chinese-NLP', 'Dataset', 'BERT', 'Knowledge-Graph']
2026-05-06 23:41:03,612 INFO __main__ Analyzing [2/3]: Our Continuation of MkDocs
2026-05-06 23:41:19,279 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-06 23:41:19,286 INFO __main__   Score: 5, Tags: ['Documentation', 'MkDocs', 'Python', 'Static Site Generator', 'Open Source']
2026-05-06 23:41:20,551 INFO __main__ Analyzing [3/3]: US government increases AI suppliers and rethinks
2026-05-06 23:41:28,819 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-06 23:41:28,820 INFO __main__   Score: 7, Tags: ['US Government', 'Defense', 'AI Suppliers', 'National Security', 'Enterprise AI']
2026-05-06 23:41:30,061 INFO __main__ Analyzed 3/3 items successfully
2026-05-06 23:41:30,061 INFO __main__ Duplicate removed: fighting41love/funNLP
2026-05-06 23:41:30,061 INFO __main__ Duplicate removed: US government increases AI suppliers and rethinks
2026-05-06 23:41:30,062 INFO __main__ Organized: 3 -> 1 items (removed 2)
2026-05-06 23:41:30,069 INFO __main__ Saved: rss-20260506-001.json
2026-05-06 23:41:30,069 INFO __main__ ============================================================
2026-05-06 23:41:30,069 INFO __main__ Pipeline completed: collected=3 analyzed=3 saved=1
2026-05-06 23:41:30,069 INFO __main__ ============================================================
2026-05-06 23:41:30,070 INFO model_client [CostTracker] minimax - calls: 3, input: 1553 tokens, output: 1026 tokens, cost: ¥0.0119
2026-05-06 23:41:30,070 INFO model_client [CostTracker] TOTAL - calls: 3, cost: ¥0.0119
```