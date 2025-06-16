import os
import json
import sqlite3
import logging
import traceback
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PROFILE_URL = os.getenv("PROFILE_URL", "https://t.me/your_profile")
SITE_URL = os.getenv("SITE_URL", "https://your.site")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# Пути
DATA_DIR = os.path.join(os.getcwd(), "data")
DATA_PATH = os.path.join(DATA_DIR, "questions.json")
DB_PATH = os.path.join(DATA_DIR, "quiz_users.db")
os.makedirs(DATA_DIR, exist_ok=True)

# Инициализация БД
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    user_id INTEGER PRIMARY KEY,
    block_idx INTEGER DEFAULT 0,
    answer_cnt INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    bonus_unlocked INTEGER DEFAULT 0,
    bonus_block_idx INTEGER DEFAULT 0,
    bonus_answer_cnt INTEGER DEFAULT 0
)
""")
conn.commit()


def get_quiz():
    try:
        with open(DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("blocks", []), data.get("bonus_blocks", [])
    except Exception as e:
        logger.error(f"Failed to load quiz data: {e}\n{traceback.format_exc()}")
        return [], []


def get_user(uid: int):
    cursor.execute(
        "SELECT block_idx, answer_cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt "
        "FROM progress WHERE user_id = ?", (uid,)
    )
    row = cursor.fetchone()
    if row:
        return list(row)
    cursor.execute("INSERT INTO progress(user_id) VALUES(?)", (uid,))
    conn.commit()
    return [0, 0, 0, 0, 0, 0]


def save_user(uid: int, block_idx: int, answer_cnt: int, score: int,
              bonus_unlocked: int = 0, bonus_block_idx: int = 0, bonus_answer_cnt: int = 0):
    cursor.execute("""
        UPDATE progress SET
          block_idx = ?, answer_cnt = ?, score = ?,
          bonus_unlocked = ?, bonus_block_idx = ?, bonus_answer_cnt = ?
        WHERE user_id = ?
    """, (block_idx, answer_cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt, uid))
    conn.commit()


def check_bonus_unlock(score: int, bonus_blocks: list) -> bool:
    return any(score >= b.get("min_score", 0) for b in bonus_blocks)


@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    uid = m.from_user and m.from_user.id
    if not uid:
        return
    save_user(uid, 0, 0, 0, 0, 0, 0)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Начать")]],
        resize_keyboard=True
    )
    await m.answer("Привет! Готов пройти викторину? Нажми «Начать»", reply_markup=kb)


@dp.message(F.text == "Начать")
async def start_quiz(m: types.Message):
    await ask_question(m.from_user.id, m.chat.id)


async def ask_question(uid: int, chat_id: int):
    blocks, bonus_blocks = get_quiz()
    block_idx, cnt, score, bonus_unlocked, _, _ = get_user(uid)

    # Предложить бонус сразу при достижении порога
    if not bonus_unlocked and check_bonus_unlock(score, bonus_blocks):
        save_user(uid, block_idx, cnt, score, 1, 0, 0)
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🎁 Открыть бонусный блок")]],
            resize_keyboard=True
        )
        return await bot.send_message(
            chat_id,
            f"🎉 Поздравляем! Вы набрали {score} баллов и открыли бонусный блок!",
            reply_markup=kb
        )

    # Если ещё есть обычные блоки
    if block_idx < len(blocks):
        block = blocks[block_idx]
        questions = block.get("questions", [])

        # Если ещё вопросы в этом блоке
        if cnt < len(questions):
            q = questions[cnt]
            opts = q.get("options", {})
            text = (
                f"📋 *{block.get('title','')}*\n\n"
                f"❓ Блок {block_idx+1}/{len(blocks)}, вопрос {cnt+1}/{len(questions)}\n\n"
                f"{q.get('text','')}\n\n"
                f"🅰️ {opts.get('A','')}\n"
                f"🅱️ {opts.get('B','')}\n"
                f"🅲 {opts.get('C','')}"
            )
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="A"), KeyboardButton(text="B"), KeyboardButton(text="C")]],
                resize_keyboard=True
            )
            return await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)

        # Если блок завершён — показываем «Следующий блок» и динамические кнопки
        buttons = block.get("buttons", {})
        kb_buttons = []
        if block_idx + 1 < len(blocks):
            kb_buttons.append([KeyboardButton(text="Следующий блок")])
        if buttons.get("gift"):
            kb_buttons.append([KeyboardButton(text="🎁 Подарок")])
        if buttons.get("site"):
            kb_buttons.append([KeyboardButton(text="🌐 Сайт")])
        if buttons.get("contacts"):
            kb_buttons.append([KeyboardButton(text="📞 Контакты")])
        kb_buttons.append([KeyboardButton(text="👤 Профиль")])
        kb = ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True)
        return await bot.send_message(
            chat_id,
            f"✅ Блок {block_idx+1} из {len(blocks)} завершён! Ваш счёт: {score}",
            reply_markup=kb
        )

    # Все обычные блоки пройдены — показываем профиль
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👤 Профиль")]],
        resize_keyboard=True
    )
    await bot.send_message(chat_id, f"🎉 Викторина завершена! Итоговый счёт: {score}", reply_markup=kb)


@dp.message(F.text.in_(["A", "B", "C"]))
async def handle_answer(m: types.Message):
    uid = m.from_user.id
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    blocks, bonus_blocks = get_quiz()

    # Ответ в обычном блоке
    if block_idx < len(blocks):
        q = blocks[block_idx]["questions"][cnt]
        score += q.get("scores", {}).get(m.text, 0)
        cnt += 1
        save_user(uid, block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt)
        await m.answer(f"✅ Ответ {m.text} принят!")
        return await ask_question(uid, m.chat.id)

    # Ответ в бонусном блоке
    if bonus_unlocked and block_idx >= len(blocks):
        return await ask_bonus_question(uid, m.chat.id)

    await m.answer("❗ Пожалуйста, нажимайте кнопку из меню")


@dp.message(F.text == "Следующий блок")
async def next_block(m: types.Message):
    uid = m.from_user.id
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    save_user(uid, block_idx + 1, 0, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt)
    await ask_question(uid, m.chat.id)


@dp.message(F.text == "👤 Профиль")
async def profile(m: types.Message):
    _, _, score, _, _, _ = get_user(m.from_user.id)
    await m.answer(f"👤 Профиль: {PROFILE_URL}\n💯 Счёт: {score} баллов")


@dp.message(F.text == "🌐 Сайт")
async def site(m: types.Message):
    await m.answer(f"🌐 Наш сайт: {SITE_URL}")


@dp.message(F.text.in_(["🎁 Подарок", "🎁 Получить подарок"]))
async def gift(m: types.Message):
    uid = m.from_user.id
    block_idx, _, _, _, _, _ = get_user(uid)
    blocks, _ = get_quiz()
    if block_idx > 0:
        prev = min(block_idx - 1, len(blocks) - 1)
        url = blocks[prev].get("buttons", {}).get("gift", "")
        if url:
            return await m.answer(f"🎁 Ваш подарок: {url}")
    await m.answer("🎁 Подарок пока недоступен")


@dp.message(F.text == "📞 Контакты")
async def contacts(m: types.Message):
    uid = m.from_user.id
    block_idx, _, _, _, _, _ = get_user(uid)
    blocks, _ = get_quiz()
    if block_idx > 0:
        prev = min(block_idx - 1, len(blocks) - 1)
        url = blocks[prev].get("buttons", {}).get("contacts", "")
        if url:
            return await m.answer(f"📞 Контакты: {url}")
    await m.answer("📞 Контакты пока недоступны")


@dp.message(F.text == "🎁 Открыть бонусный блок")
async def open_bonus(m: types.Message):
    await ask_bonus_question(m.from_user.id, m.chat.id)


        return await bot.send_message(
            chat_id,
            f"🎉 Все бонусные блоки завершены! Итоговый счёт: {score}",
            reply_markup=kb
        )
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="👤 Профиль")]],
            resize_keyboard=True
        )
        return await bot.send_message(chat_id, f"🎉 Бонусный блок завершён! Итоговый счёт: {score}", reply_markup=kb)

    block = bonus_blocks[b_block_idx]
    questions = block.get("questions", [])

    if b_ans_cnt < len(questions):
        q = questions[b_ans_cnt]
        opts = q.get("options", {})
        text = (
            f"🎁 *{block.get('title','')}*\n\n"
            f"{q.get('text','')}\n\n"
            f"🅰️ {opts.get('A','')}\n"
            f"🅱️ {opts.get('B','')}\n"
            f"🅲 {opts.get('C','')}"
        )
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="A"), KeyboardButton(text="B"), KeyboardButton(text="C")]],
            resize_keyboard=True
        )
        return await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)

    save_user(uid, len(get_quiz()[0]), 0, score, 1, b_block_idx + 1, 0)
    return await ask_bonus_question(uid, chat_id)


@dp.message()
async def fallback(m: types.Message):
    await m.answer("❗ Пожалуйста, выберите кнопку из меню")


async def main():
    logger.info("Starting bot…")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    conn.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
async def ask_bonus_question(uid: int, chat_id: int):
    _, bonus_blocks = get_quiz()
    _, _, score, _, b_block_idx, b_ans_cnt = get_user(uid)
    
    # Если все бонусные блоки пройдены
    if b_block_idx >= len(bonus_blocks):
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="👤 Профиль")]],
            resize_keyboard=True
        )
        return await bot.send_message(
            chat_id, 
            f"🎉 Все бонусные блоки завершены! Итоговый счёт: {score}", 
            reply_markup=kb
        )
    
    block = bonus_blocks[b_block_idx]
    questions = block.get("questions", [])
    
    # Если есть вопросы в текущем бонусном блоке
    if b_ans_cnt < len(questions):
        q = questions[b_ans_cnt]
        opts = q.get("options", {})
        text = (
            f"🎁 *{block.get('title','')}*\n\n"
            f"❓ Бонусный блок {b_block_idx+1}/{len(bonus_blocks)}, вопрос {b_ans_cnt+1}/{len(questions)}\n\n"
            f"{q.get('text','')}\n\n"
            f"🅰 {opts.get('A','')}\n"
            f"🅱 {opts.get('B','')}\n"
            f"🅲 {opts.get('C','')}"
        )
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="A"), KeyboardButton(text="B"), KeyboardButton(text="C")]],
            resize_keyboard=True
        )
        return await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)
    
    # Текущий бонусный блок завершён
    buttons = block.get("buttons", {})
    kb_buttons = []
    
    # Проверяем, есть ли следующий бонусный блок
    if b_block_idx + 1 < len(bonus_blocks):
        next_bonus = bonus_blocks[b_block_idx + 1]
        if score >= next_bonus.get("min_score", 0):
            kb_buttons.append([KeyboardButton(text="🎁 Следующий бонусный блок")])
    
    # Добавляем кнопки текущего блока
    if buttons.get("gift"):
        kb_buttons.append([KeyboardButton(text="🎁 Подарок")])
    if buttons.get("site"):
        kb_buttons.append([KeyboardButton(text="🌐 Сайт")])
    if buttons.get("contacts"):
        kb_buttons.append([KeyboardButton(text="📞 Контакты")])
    
    kb_buttons.append([KeyboardButton(text="👤 Профиль")])
    
    kb = ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True)
    
    await bot.send_message(
        chat_id,
        f"✅ Бонусный блок {b_block_idx+1} завершён! Ваш счёт: {score}",
        reply_markup=kb
    )

@dp.message(F.text == "🎁 Следующий бонусный блок")
async def next_bonus_block(m: types.Message):
    uid = m.from_user.id
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    save_user(uid, block_idx, cnt, score, bonus_unlocked, bonus_block_idx + 1, 0)
    await ask_bonus_question(uid, m.chat.id)
