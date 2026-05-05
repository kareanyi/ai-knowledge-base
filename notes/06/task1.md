millerlin@192 v2 % uv run python pipeline/model_client.py
Testing with prompt: 用一句话解释量子计算
--------------------------------------------------
2026-05-05 22:12:10,904 INFO HTTP Request: POST https://api.minimax.chat/v1/chat/completions "HTTP/1.1 200 OK"
2026-05-05 22:12:10,957 INFO [minimax] prompt_tokens=26 completion_tokens=72 cost=0.000386 USD
Response: <think>用户要求用一句话解释量子计算。这是一个相对简单的请求，但我应该确保解释清晰、准确且易于理解。量子计算是一个复杂的概念，我需要用简洁的语言捕捉其核心特点。</think>

量子计算是一种利用量子力学原理（如叠加和纠缠）在量子比特上同时进行多种计算的计算方式，相比传统计算机能更高效地解决某些复杂问题。
millerlin@192 v2 %