import os
from dotenv import load_dotenv
import asyncio
from aiogram import Bot

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def test():
	bot = Bot(BOT_TOKEN)
	try:
		me = await bot.get_me()
		print(f"✅ Бот работает: @{me.username}")
	except Exception as e:
		print(f"❌ Ошибка: {e}")
	finally:
		await bot.session.close()

asyncio.run(test())
