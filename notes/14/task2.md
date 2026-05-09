## 测试

```shell
millerlin@192 v4-production % uv run python3 -c "
import asyncio
from distribution.publisher import publish_daily_digest

async def test():
    results = await publish_daily_digest(
        knowledge_dir='knowledge/articles',
        date='2026-04-11',  # 改成你知识库里有数据的日期
        channels=['telegram']
    )
    for r in results:
        status = '✅' if r.success else '❌'
        print(f'{status} {r.channel}: {r.message_id or r.error}')

asyncio.run(test())
"
TelegramPublisher: TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 未设置
Telegram 消息发送失败: Not Found
❌ telegram: Not Found
millerlin@192 v4-production %
```