@dp.message(F.text.in_(["A", "B", "C"]))
async def handle_answer(m: types.Message):
    if not m.from_user:
        return
    
    uid = m.from_user.id
    choice = m.text
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    blocks, bonus_blocks = get_quiz()
    
    logger.info(f"User {uid} answered {choice}")
    
    # Основные блоки
    if not blocks or block_idx >= len(blocks):
        return await m.answer("❌ Ошибка: викторина недоступна")

    questions = blocks[block_idx]["questions"]
    if cnt >= len(questions):
        return await m.answer("❌ Блок уже завершён")

    question = questions[cnt]
    scores = question.get("scores", {"A": 1, "B": 2, "C": 3})
    score += scores.get(choice, 1)
    cnt += 1

    save_user(uid, block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt)
    await m.answer(f"✅ Ответ {choice} принят!")

    if cnt < len(questions):
        await ask_question(uid, m.chat.id)
        return

    # Завершили блок
    next_idx = block_idx + 1
    save_user(uid, next_idx, 0, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt)

    kb_buttons = []
    if next_idx < len(blocks):
        kb_buttons.append([KeyboardButton(text="Следующий блок")])

    btns = blocks[block_idx].get("buttons", {})
    if btns.get("gift"):
        kb_buttons.append([KeyboardButton(text="🎁 Подарок")])
    if btns.get("site"):
        kb_buttons.append([KeyboardButton(text="🌐 Сайт")])
    if btns.get("contacts"):
        kb_buttons.append([KeyboardButton(text="📞 Контакты")])

    kb_buttons.append([KeyboardButton(text="👤 Профиль")])
    kb = ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True)

    await m.answer(f"🎉 Блок завершён! Ваш счёт: {score} баллов\n\nВыберите действие:", reply_markup=kb)

@dp.message(F.text == "Следующий блок")
async def next_block(m: types.Message):
    if not m.from_user:
        return
    await ask_question(m.from_user.id, m.chat.id)

@dp.message(F.text == "👤 Профиль")
async def profile(m: types.Message):
    if not m.from_user:
        return
    uid = m.from_user.id
    _, _, score, _, _, _ = get_user(uid)
    await m.answer(f"👤 Ваш профиль: {PROFILE_URL}\n💯 Ваш счёт: {score} баллов")

@dp.message(F.text == "🌐 Сайт")
async def site(m: types.Message):
    await m.answer(f"🌐 Наш сайт: {SITE_URL}")

@dp.message(F.text.in_(["🎁 Подарок", "🎁 Получить подарок"]))
async def gift(m: types.Message):
    if not m.from_user:
        return
    uid = m.from_user.id
    block_idx, _, _, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    blocks, bonus_blocks = get_quiz()

    # Обычный подарок
    if block_idx > 0:
        prev = min(block_idx - 1, len(blocks) - 1)
        url = blocks[prev].get("buttons", {}).get("gift", "")
        if url:
            return await m.answer(f"🎁 Ваш подарок: {url}")

    await m.answer("🎁 Подарок пока недоступен")

@dp.message(F.text == "📞 Контакты")
async def contacts(m: types.Message):
    if not m.from_user:
        return
    uid = m.from_user.id
    block_idx, _, _, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    blocks, bonus_blocks = get_quiz()

    # Обычные контакты
    if block_idx > 0:
        prev = min(block_idx - 1, len(blocks) - 1)
        url = blocks[prev].get("buttons", {}).get("contacts", "")
        if url:
            return await m.answer(f"📞 Контакты: {url}")

    await m.answer("📞 Контакты пока недоступны")

@dp.message()
async def fallback(m: types.Message):
    await m.answer("❗ Выберите одну из кнопок на клавиатуре")

async def main():
    try:
        logger.info("Starting bot...")
        blocks, bonus_blocks = get_quiz()
        logger.info(f"Bot starting with {len(blocks)} blocks and {len(bonus_blocks)} bonus blocks")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        conn.close()


# Обработчики бонусных блоков
@dp.message(F.text == "🎁 Открыть бонусный блок")
async def unlock_bonus_block(m: types.Message):
    if not m.from_user:
        return
    
    uid = m.from_user.id
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    blocks, bonus_blocks = get_quiz()
    
    logger.info(f"User {uid} wants to unlock bonus block. Score: {score}")
    
    if not bonus_blocks:
        await m.answer("❌ Бонусные блоки недоступны")
        return
    
    # Проверяем доступ к бонусным блокам
    available_bonus = None
    for bonus_block in bonus_blocks:
        min_score = bonus_block.get('min_score', 0)
        if score >= min_score:
            available_bonus = bonus_block
            break
    
    if not available_bonus:
        await m.answer(f"❌ Для доступа к бонусному блоку нужно набрать больше баллов.\nВаш счёт: {score}")
        return
    
    # Разблокируем бонусный блок
    save_user(uid, block_idx, cnt, score, 1, 0, 0)  # bonus_unlocked = 1
    
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🎁 Начать бонусный блок")]],
        resize_keyboard=True
    )
    
    await m.answer(
        f"🎉 Бонусный блок разблокирован!\n\n"
        f"📋 *{available_bonus.get('title', 'Бонусный блок')}*\n\n"
        f"Готовы начать?",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.message(F.text == "🎁 Начать бонусный блок")
async def start_bonus_quiz(m: types.Message):
    if not m.from_user:
        return
    await ask_bonus_question(m.from_user.id, m.chat.id)

async def ask_bonus_question(user_id: int, chat_id: int):
    logger.info(f"Asking bonus question for user {user_id}")
    
    blocks, bonus_blocks = get_quiz()
    if not bonus_blocks:
        await bot.send_message(chat_id, "❌ Бонусные блоки недоступны")
        return
    
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(user_id)
    
    # Проверяем разблокирован ли бонусный блок
    if not bonus_unlocked:
        await bot.send_message(chat_id, "❌ Бонусный блок не разблокирован")
        return
    
    # Находим доступный бонусный блок
    available_bonus = None
    for bonus_block in bonus_blocks:
        min_score = bonus_block.get('min_score', 0)
        if score >= min_score:
            available_bonus = bonus_block
            break
    
    if not available_bonus:
        await bot.send_message(chat_id, "❌ Бонусный блок недоступен")
        return
    
    questions = available_bonus.get("questions", [])
    
    # Если бонусный блок завершён
    if bonus_answer_cnt >= len(questions):
        kb_buttons = []
        btns = available_bonus.get("buttons", {})
        if btns.get("gift"):
            kb_buttons.append([KeyboardButton(text="🎁 Бонусный подарок")])
        if btns.get("site"):
            kb_buttons.append([KeyboardButton(text="🌐 Бонусный сайт")])
        if btns.get("contacts"):
            kb_buttons.append([KeyboardButton(text="📞 Бонусные контакты")])
        kb_buttons.append([KeyboardButton(text="👤 Профиль")])
        
        kb = ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True)
        await bot.send_message(
            chat_id, 
            f"🎉 Бонусный блок завершён!\nВаш итоговый счёт: {score} баллов",
            reply_markup=kb
        )
        return
    
    question = questions[bonus_answer_cnt]
    options = question.get("options", {})
    
    text = f"🎁 *{available_bonus.get('title', 'Бонусный блок')}*\n\n"
    text += f"❓ *Бонусный вопрос {bonus_answer_cnt + 1} из {len(questions)}*\n\n"
    text += f"{question.get('text', '')}\n\n"
    text += f"🅰 {options.get('A', 'Вариант A')}\n\n"
    text += f"🅱 {options.get('B', 'Вариант B')}\n\n"
    text += f"🅲 {options.get('C', 'Вариант C')}"
    
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="A"), KeyboardButton(text="B"), KeyboardButton(text="C")]],
        resize_keyboard=True
    )
    
    await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)

# Обработчики для бонусных кнопок
@dp.message(F.text == "🎁 Бонусный подарок")
async def bonus_gift(m: types.Message):
    if not m.from_user:
        return
    
    uid = m.from_user.id
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    blocks, bonus_blocks = get_quiz()
    
    if not bonus_unlocked or not bonus_blocks:
        await m.answer("🎁 Бонусный подарок недоступен")
        return
    
    # Находим доступный бонусный блок
    for bonus_block in bonus_blocks:
        min_score = bonus_block.get('min_score', 0)
        if score >= min_score:
            url = bonus_block.get("buttons", {}).get("gift", "")
            if url:
                await m.answer(f"🎁 Ваш бонусный подарок: {url}")
                return
    
    await m.answer("🎁 Бонусный подарок пока недоступен")

@dp.message(F.text == "🌐 Бонусный сайт")
async def bonus_site(m: types.Message):
    if not m.from_user:
        return
    
    uid = m.from_user.id
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    blocks, bonus_blocks = get_quiz()
    
    if not bonus_unlocked or not bonus_blocks:
        await m.answer("🌐 Бонусный сайт недоступен")
        return
    
    for bonus_block in bonus_blocks:
        min_score = bonus_block.get('min_score', 0)
        if score >= min_score:
            url = bonus_block.get("buttons", {}).get("site", "")
            if url:
                await m.answer(f"🌐 Бонусный сайт: {url}")
                return
    
    await m.answer("🌐 Бонусный сайт пока недоступен")

@dp.message(F.text == "📞 Бонусные контакты")
async def bonus_contacts(m: types.Message):
    if not m.from_user:
        return
    
    uid = m.from_user.id
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    blocks, bonus_blocks = get_quiz()
    
    if not bonus_unlocked or not bonus_blocks:
        await m.answer("📞 Бонусные контакты недоступны")
        return
    
    for bonus_block in bonus_blocks:
        min_score = bonus_block.get('min_score', 0)
        if score >= min_score:
            url = bonus_block.get("buttons", {}).get("contacts", "")
            if url:
                await m.answer(f"📞 Бонусные контакты: {url}")
                return
    
    await m.answer("📞 Бонусные контакты пока недоступны")

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)