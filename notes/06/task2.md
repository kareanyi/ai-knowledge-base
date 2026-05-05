## dry-run
```shell
millerlin@192 v2 % uv run python pipeline/pipeline.py --sources github --limit 5 --dry-run
2026-05-05 22:26:07,290 INFO __main__ ============================================================
2026-05-05 22:26:07,290 INFO __main__ Pipeline started: sources=['github'] limit=5 dry_run=True
2026-05-05 22:26:07,290 INFO __main__ ============================================================
2026-05-05 22:26:07,346 INFO __main__ Loaded 0 existing URLs for deduplication
2026-05-05 22:26:07,346 INFO __main__ Collecting GitHub repositories: https://api.github.com/search/repositories
2026-05-05 22:26:09,309 INFO httpx HTTP Request: GET https://api.github.com/search/repositories?q=AI+OR+artificial+intelligence+OR+LLM+OR+large+language+model+OR+GPT+OR+machine+learning&sort=stars&order=desc&per_page=5 "HTTP/1.1 200 OK"
2026-05-05 22:26:09,328 INFO __main__ Collected 5 GitHub repositories
2026-05-05 22:26:09,334 INFO __main__ Raw data saved to: /Users/millerlin/Codes/local/opencode-workspace/action-camp/ai-knowledge-base/v2/knowledge/raw/2026-05-05-raw.json
2026-05-05 22:26:09,334 INFO __main__ [DRY-RUN] Skipping analysis and save
millerlin@192 v2 % uv run python pipeline/pipeline.py --sources github,rss --limit 10 --dry-run
2026-05-05 22:26:22,742 INFO __main__ ============================================================
2026-05-05 22:26:22,742 INFO __main__ Pipeline started: sources=['github', 'rss'] limit=10 dry_run=True
2026-05-05 22:26:22,742 INFO __main__ ============================================================
2026-05-05 22:26:22,789 INFO __main__ Loaded 0 existing URLs for deduplication
2026-05-05 22:26:22,790 INFO __main__ Collecting GitHub repositories: https://api.github.com/search/repositories
2026-05-05 22:26:24,340 INFO httpx HTTP Request: GET https://api.github.com/search/repositories?q=AI+OR+artificial+intelligence+OR+LLM+OR+large+language+model+OR+GPT+OR+machine+learning&sort=stars&order=desc&per_page=10 "HTTP/1.1 200 OK"
2026-05-05 22:26:25,654 INFO __main__ Collected 10 GitHub repositories
2026-05-05 22:26:25,655 INFO __main__ Collecting RSS feed: https://hnrss.org/frontpage
2026-05-05 22:26:28,723 INFO httpx HTTP Request: GET https://hnrss.org/frontpage "HTTP/1.1 200 OK"
2026-05-05 22:26:28,727 INFO __main__ Collected 10 items from https://hnrss.org/frontpage
2026-05-05 22:26:28,727 INFO __main__ Collecting RSS feed: https://feeds.feedburner.com/oreilly radar
2026-05-05 22:26:30,838 INFO httpx HTTP Request: GET https://feeds.feedburner.com/oreilly%20radar "HTTP/1.1 404 Not Found"
2026-05-05 22:26:31,058 WARNING __main__ RSS feed request failed for https://feeds.feedburner.com/oreilly radar: Client error '404 Not Found' for url 'https://feeds.feedburner.com/oreilly%20radar'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-05-05 22:26:31,058 INFO __main__ Collecting RSS feed: https://www.artificialintelligence-news.com/feed/
2026-05-05 22:26:33,433 INFO httpx HTTP Request: GET https://www.artificialintelligence-news.com/feed/ "HTTP/1.1 200 OK"
2026-05-05 22:26:34,125 INFO __main__ Collected 10 items from https://www.artificialintelligence-news.com/feed/
2026-05-05 22:26:34,126 INFO __main__ Collected 20 items from RSS feeds
2026-05-05 22:26:34,129 INFO __main__ Raw data saved to: /Users/millerlin/Codes/local/opencode-workspace/action-camp/ai-knowledge-base/v2/knowledge/raw/2026-05-05-raw.json
2026-05-05 22:26:34,129 INFO __main__ [DRY-RUN] Skipping analysis and save
```

## normal

```shell
millerlin@192 v2 % uv run python pipeline/pipeline.py --sources github,rss --limit 5
2026-05-05 22:28:06,379 INFO __main__ ============================================================
2026-05-05 22:28:06,379 INFO __main__ Pipeline started: sources=['github', 'rss'] limit=5 dry_run=False
2026-05-05 22:28:06,379 INFO __main__ ============================================================
2026-05-05 22:28:06,433 INFO __main__ Loaded 0 existing URLs for deduplication
2026-05-05 22:28:06,433 INFO __main__ Collecting GitHub repositories: https://api.github.com/search/repositories
2026-05-05 22:28:08,313 INFO httpx HTTP Request: GET https://api.github.com/search/repositories?q=AI+OR+artificial+intelligence+OR+LLM+OR+large+language+model+OR+GPT+OR+machine+learning&sort=stars&order=desc&per_page=5 "HTTP/1.1 200 OK"
2026-05-05 22:28:08,538 INFO __main__ Collected 5 GitHub repositories
2026-05-05 22:28:08,538 INFO __main__ Collecting RSS feed: https://hnrss.org/frontpage
2026-05-05 22:28:10,984 INFO httpx HTTP Request: GET https://hnrss.org/frontpage "HTTP/1.1 200 OK"
2026-05-05 22:28:10,987 INFO __main__ Collected 5 items from https://hnrss.org/frontpage
2026-05-05 22:28:10,987 INFO __main__ Collecting RSS feed: https://feeds.feedburner.com/oreilly radar
2026-05-05 22:28:12,764 INFO httpx HTTP Request: GET https://feeds.feedburner.com/oreilly%20radar "HTTP/1.1 404 Not Found"
2026-05-05 22:28:12,968 WARNING __main__ RSS feed request failed for https://feeds.feedburner.com/oreilly radar: Client error '404 Not Found' for url 'https://feeds.feedburner.com/oreilly%20radar'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-05-05 22:28:12,969 INFO __main__ Collecting RSS feed: https://www.artificialintelligence-news.com/feed/
2026-05-05 22:28:15,419 INFO httpx HTTP Request: GET https://www.artificialintelligence-news.com/feed/ "HTTP/1.1 200 OK"
2026-05-05 22:28:16,084 INFO __main__ Collected 5 items from https://www.artificialintelligence-news.com/feed/
2026-05-05 22:28:16,085 INFO __main__ Collected 10 items from RSS feeds
2026-05-05 22:28:16,087 INFO __main__ Raw data saved to: /Users/millerlin/Codes/local/opencode-workspace/action-camp/ai-knowledge-base/v2/knowledge/raw/2026-05-05-raw.json
2026-05-05 22:28:16,087 INFO __main__ Analyzing [1/15]: fighting41love/funNLP
2026-05-05 22:28:46,683 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:28:46,912 INFO __main__   Score: 9, Tags: ['NLP', 'Chinese-NLP', 'Text-Processing', 'BERT', 'Dataset']
2026-05-05 22:28:47,613 INFO __main__ Analyzing [2/15]: huggingface/trl
2026-05-05 22:29:03,054 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:29:03,060 INFO __main__   Score: 9, Tags: ['RLHF', 'LLM', 'Fine-tuning', 'Reinforcement Learning', 'Hugging Face']
2026-05-05 22:29:04,394 INFO __main__ Analyzing [3/15]: apache/brpc
2026-05-05 22:29:12,296 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:29:12,300 INFO __main__   Score: 9, Tags: ['RPC', 'C++', 'Distributed Systems', 'Apache', 'High Performance']
2026-05-05 22:29:13,443 INFO __main__ Analyzing [4/15]: graykode/nlp-tutorial
2026-05-05 22:29:27,420 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:29:27,424 INFO __main__   Score: 8, Tags: ['NLP', 'Deep Learning', 'PyTorch', 'TensorFlow', 'Transformer']
2026-05-05 22:29:28,473 INFO __main__ Analyzing [5/15]: gunthercox/ChatterBot
2026-05-05 22:29:46,913 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:29:46,921 INFO __main__   Score: 8, Tags: ['Chatbot', 'NLP', 'Machine Learning', 'Python', 'Conversation AI']
2026-05-05 22:29:47,700 INFO __main__ Analyzing [6/15]: AI didn't delete your database, you did
2026-05-05 22:30:08,672 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:30:08,677 INFO __main__   Score: 6, Tags: ['AI', 'Accountability', 'Database', 'Software Engineering', 'DevOps']
2026-05-05 22:30:09,655 INFO __main__ Analyzing [7/15]: Simple Meta-Harness on Islo.dev
2026-05-05 22:30:22,354 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:30:23,152 INFO __main__   Score: 5, Tags: ['Testing', 'Harness', 'Framework', 'DevTools', 'Meta-Programming']
2026-05-05 22:30:23,993 INFO __main__ Analyzing [8/15]: Google, Microsoft and xAI Agree to Share Early AI
2026-05-05 22:30:47,454 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:30:47,457 INFO __main__   Score: 7, Tags: ['AI Regulation', 'Government Policy', 'AI Safety', 'Tech Industry', 'AI Governance']
2026-05-05 22:30:48,044 INFO __main__ Analyzing [9/15]: AI Product Graveyard
2026-05-05 22:31:00,183 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:31:00,408 INFO __main__   Score: 7, Tags: ['AI Products', 'Failure Analysis', 'Product Management', 'Startup Insights', 'Industry Trends']
2026-05-05 22:31:00,983 INFO __main__ Analyzing [10/15]: iOS 27 is adding a 'Create a Pass' button to Apple
2026-05-05 22:31:21,315 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:31:21,552 INFO __main__   Score: 5, Tags: ['Apple', 'iOS', 'Wallet', 'PassKit', 'Mobile']
2026-05-05 22:31:22,923 INFO __main__ Analyzing [11/15]: Physical AI raises governance questions for autono
2026-05-05 22:31:39,575 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:31:39,577 INFO __main__   Score: 6, Tags: ['Physical AI', 'Autonomous Systems', 'Robotics Governance', 'Industrial AI', 'AI Safety']
2026-05-05 22:31:40,262 INFO __main__ Analyzing [12/15]: Google made agentic AI governance a product. Enter
2026-05-05 22:32:05,572 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:32:05,573 INFO __main__   Score: 7, Tags: ['Agentic AI', 'AI Governance', 'Enterprise AI', 'Google Cloud', 'AI Compliance']
2026-05-05 22:32:06,403 INFO __main__ Analyzing [13/15]: SAP: How enterprise AI governance secures profit m
2026-05-05 22:32:24,752 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:32:24,966 INFO __main__   Score: 6, Tags: ['AI Governance', 'Enterprise AI', 'SAP', 'Business Automation', 'Enterprise Software']
2026-05-05 22:32:25,705 INFO __main__ Analyzing [14/15]: Per-token AI charges come to GitHub Copilot
2026-05-05 22:32:40,599 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:32:40,603 WARNING __main__ JSON parse failed for rss-820912: Extra data: line 9 column 1 (char 750)
2026-05-05 22:32:41,784 INFO __main__ Analyzing [15/15]: What LG and NVIDIA’s talks reveal about the future
2026-05-05 22:32:59,748 INFO httpx HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:33:00,526 INFO __main__   Score: 7, Tags: ['Physical AI', 'Robotics', 'Smart Mobility', 'Data Centers', 'B2B Partnership']
2026-05-05 22:33:01,566 INFO __main__ Analyzed 14/15 items successfully
2026-05-05 22:33:01,568 INFO __main__ Organized: 14 -> 14 items (removed 0)
2026-05-05 22:33:01,573 INFO __main__ Saved: b7c075cc-c864-4f8b-8d2f-490ae3808e3d.json
2026-05-05 22:33:01,574 INFO __main__ Saved: 22366497-af71-4bef-938e-36bf08316171.json
2026-05-05 22:33:01,577 INFO __main__ Saved: 326c826b-7245-4809-ac82-a4639170f2e1.json
2026-05-05 22:33:01,578 INFO __main__ Saved: 386d4d1b-0b8e-4491-b810-28c1569c37b3.json
2026-05-05 22:33:01,579 INFO __main__ Saved: 964d17b9-4f09-402b-8ace-ff754c2376b1.json
2026-05-05 22:33:01,580 INFO __main__ Saved: 00271234-18b0-4dab-bd71-243b4e7eefa5.json
2026-05-05 22:33:01,581 INFO __main__ Saved: 6ffd99d7-5c14-436b-b4e1-1387f45c02d0.json
2026-05-05 22:33:01,582 INFO __main__ Saved: 9a048f0d-432d-4468-a885-40e142f16728.json
2026-05-05 22:33:01,583 INFO __main__ Saved: 225a5028-5ea6-4604-b1bb-79d24642d25d.json
2026-05-05 22:33:01,583 INFO __main__ Saved: f636b6ec-4b70-4f78-ac38-da284afaa47e.json
2026-05-05 22:33:01,584 INFO __main__ Saved: ec19f8f4-4f0e-4eb3-b86d-87de4cb9066b.json
2026-05-05 22:33:01,584 INFO __main__ Saved: 6db8cdfa-a59c-46cf-9f9f-b526a5f15a82.json
2026-05-05 22:33:01,585 INFO __main__ Saved: 2096c995-b673-4139-9f62-fef80b6b81cd.json
2026-05-05 22:33:01,586 INFO __main__ Saved: b1c05163-7472-47ac-9092-ffb5ed2c9248.json
2026-05-05 22:33:01,586 INFO __main__ ============================================================
2026-05-05 22:33:01,586 INFO __main__ Pipeline completed: collected=15 analyzed=14 saved=14
2026-05-05 22:33:01,586 INFO __main__ ============================================================
```