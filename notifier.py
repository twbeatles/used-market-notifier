import telegram
import asyncio
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class Notifier:
    def __init__(self):
        self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        self.chat_id = TELEGRAM_CHAT_ID

    async def send_message(self, text):
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text)
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")

    async def send_new_item(self, item):
        message = (
            f"🥕 [{item.platform}] 키워드: {item.keyword}\n"
            f"제목: {item.title}\n"
            f"가격: {item.price}\n"
            f"링크: {item.link}"
        )
        await self.send_message(message)

if __name__ == "__main__":
    # Test
    async def test():
        n = Notifier()
        await n.send_message("Validator initialized.")
    asyncio.run(test())
