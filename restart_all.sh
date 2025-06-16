#!/usr/bin/env bash
cd "$(dirname "$0")"

# 1. Остановим всё
pkill -f bot.py || true
pkill -f app.py || true
pkill -f "flask run" || true

# 2. Активируем виртуальное окружение
source venv/bin/activate

# 3. Запускаем админку в фоне
nohup python app.py > logs/admin.log 2>&1 &

# 4. Ждем 2 секунды
sleep 2

# 5. Запускаем бота в фоне
nohup python bot.py > logs/bot.log 2>&1 &

echo "→ Все сервисы перезапущены. Логи: logs/admin.log, logs/bot.log"
