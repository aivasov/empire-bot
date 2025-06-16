import os
from dotenv import load_dotenv

print("=== ПРОВЕРКА .ENV ===")
print(f"Файл .env существует: {os.path.exists('.env')}")

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROFILE_URL = os.getenv("PROFILE_URL")
SITE_URL = os.getenv("SITE_URL")

print(f"BOT_TOKEN загружен: {'Да' if BOT_TOKEN else 'НЕТ'}")
if BOT_TOKEN:
	print(f"BOT_TOKEN начинается с: {BOT_TOKEN[:10]}...")
else:
	print("❌ BOT_TOKEN пустой!")

print(f"PROFILE_URL: {PROFILE_URL}")
print(f"SITE_URL: {SITE_URL}")
