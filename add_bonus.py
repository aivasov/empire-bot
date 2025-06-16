import re

# Читаем оригинальный файл
with open('/home/bot/empire-bot/bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Добавляем обработку бонусных ответов в handle_answer
bonus_check = '''
    # Проверяем, отвечаем ли мы на бонусный вопрос
    if bonus_unlocked:
        # Находим доступный бонусный блок
        available_bonus = None
        for bonus_block in bonus_blocks:
            min_score_needed = bonus_block.get('min_score', 0)
            if score >= min_score_needed:
                available_bonus = bonus_block
                break
        
        if available_bonus:
            bonus_questions = available_bonus.get("questions", [])
            if bonus_answer_cnt < len(bonus_questions):
                # Обрабатываем бонусный ответ
                bonus_question = bonus_questions[bonus_answer_cnt]
                bonus_scores = bonus_question.get("scores", {"A": 1, "B": 2, "C": 3})
                score += bonus_scores.get(choice, 1)
                bonus_answer_cnt += 1
                
                save_user(uid, block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt)
                await m.answer(f"✅ Бонусный ответ {choice} принят!")
                
                if bonus_answer_cnt < len(bonus_questions):
                    # Следующий бонусный вопрос
                    await ask_bonus_question(uid, m.chat.id)
                else:
                    # Бонусный блок завершён
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
                    await m.answer(f"🎉 Бонусный блок завершён! Итоговый счёт: {score} баллов", reply_markup=kb)
                return'''

# Вставляем проверку бонусов после логирования
pattern = r'(logger\.info\(f"User {uid} answered {choice}"\))'
content = re.sub(pattern, r'\1' + bonus_check, content)

# 2. Добавляем бонусные обработчики перед if __name__ == "__main__":
bonus_handlers = '''
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
        await m.answer(f"❌ Для доступа к бонусному блоку нужно набрать больше баллов.\\nВаш счёт: {score}")
        return
    
    # Разблокируем бонусный блок
    save_user(uid, block_idx, cnt, score, 1, 0, 0)  # bonus_unlocked = 1
    
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🎁 Начать бонусный блок")]],
        resize_keyboard=True
    )
    
    await m.answer(
        f"🎉 Бонусный блок разблокирован!\\n\\n"
        f"📋 *{available_bonus.get('title', 'Бонусный блок')}*\\n\\n"
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
            f"🎉 Бонусный блок завершён!\\nВаш итоговый счёт: {score} баллов",
            reply_markup=kb
        )
        return
    
    question = questions[bonus_answer_cnt]
    options = question.get("options", {})
    
    text = f"🎁 *{available_bonus.get('title', 'Бонусный блок')}*\\n\\n"
    text += f"❓ *Бонусный вопрос {bonus_answer_cnt + 1} из {len(questions)}*\\n\\n"
    text += f"{question.get('text', '')}\\n\\n"
    text += f"🅰 {options.get('A', 'Вариант A')}\\n\\n"
    text += f"🅱 {options.get('B', 'Вариант B')}\\n\\n"
    text += f"🅲 {options.get('C', 'Вариант C')}"
    
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="A"), KeyboardButton(text="B"), KeyboardButton(text="C")]],
        resize_keyboard=True
    )
    
    await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)

'''

# Вставляем обработчики перед main
content = re.sub(r'(if __name__ == "__main__":)', bonus_handlers + r'\1', content)

# 3. Модифицируем функцию ask_question для добавления кнопки бонусного блока
pattern = r'(kb_buttons\.append\(\[KeyboardButton\(text="👤 Профиль"\)\]\))'
bonus_button_code = '''        # Проверяем доступность бонусного блока
        if bonus_blocks and not bonus_unlocked:
            for bonus_block in bonus_blocks:
                min_score = bonus_block.get("min_score", 0)
                if score >= min_score:
                    kb_buttons.append([KeyboardButton(text="🎁 Открыть бонусный блок")])
                    break
        '''

content = re.sub(pattern, bonus_button_code + r'\1', content)

# Записываем исправленный файл
with open('/home/bot/empire-bot/bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Бонусная функциональность добавлена!")
