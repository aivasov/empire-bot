# Читаем оригинальный файл
with open('/home/bot/empire-bot/bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим место для вставки бонусной логики в handle_answer
handle_answer_addition = '''
    # Проверяем бонусный режим
    if bonus_unlocked:
        available_bonus = None
        for bonus_block in bonus_blocks:
            if score >= bonus_block.get('min_score', 0):
                available_bonus = bonus_block
                break
        
        if available_bonus and bonus_answer_cnt < len(available_bonus.get("questions", [])):
            # Обрабатываем бонусный ответ
            bonus_question = available_bonus["questions"][bonus_answer_cnt]
            bonus_scores = bonus_question.get("scores", {"A": 1, "B": 2, "C": 3})
            score += bonus_scores.get(choice, 1)
            bonus_answer_cnt += 1
            
            save_user(uid, block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt)
            await m.answer(f"✅ Бонусный ответ {choice} принят!")
            
            if bonus_answer_cnt < len(available_bonus["questions"]):
                await ask_bonus_question(uid, m.chat.id)
            else:
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
                await m.answer(f"🎉 Бонусный блок завершён! Счёт: {score}", reply_markup=kb)
            return
'''

# Вставляем после логирования в handle_answer
content = content.replace(
    'logger.info(f"User {uid} answered {choice}")',
    'logger.info(f"User {uid} answered {choice}")' + handle_answer_addition
)

# Добавляем бонусные обработчики перед main
bonus_handlers = '''
@dp.message(F.text == "🎁 Открыть бонусный блок")
async def unlock_bonus_block(m: types.Message):
    if not m.from_user:
        return
    
    uid = m.from_user.id
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(uid)
    blocks, bonus_blocks = get_quiz()
    
    if not bonus_blocks:
        await m.answer("❌ Бонусные блоки недоступны")
        return
    
    available_bonus = None
    for bonus_block in bonus_blocks:
        if score >= bonus_block.get('min_score', 0):
            available_bonus = bonus_block
            break
    
    if not available_bonus:
        await m.answer(f"❌ Нужно больше баллов. Ваш счёт: {score}")
        return
    
    save_user(uid, block_idx, cnt, score, 1, 0, 0)
    
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🎁 Начать бонусный блок")]],
        resize_keyboard=True
    )
    
    await m.answer(
        f"🎉 Бонусный блок разблокирован!\\n\\n{available_bonus.get('title', 'Бонус')}\\n\\nГотовы начать?",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.message(F.text == "🎁 Начать бонусный блок")
async def start_bonus_quiz(m: types.Message):
    if not m.from_user:
        return
    await ask_bonus_question(m.from_user.id, m.chat.id)

async def ask_bonus_question(user_id: int, chat_id: int):
    blocks, bonus_blocks = get_quiz()
    if not bonus_blocks:
        await bot.send_message(chat_id, "❌ Бонусные блоки недоступны")
        return
    
    block_idx, cnt, score, bonus_unlocked, bonus_block_idx, bonus_answer_cnt = get_user(user_id)
    
    if not bonus_unlocked:
        await bot.send_message(chat_id, "❌ Бонусный блок не разблокирован")
        return
    
    available_bonus = None
    for bonus_block in bonus_blocks:
        if score >= bonus_block.get('min_score', 0):
            available_bonus = bonus_block
            break
    
    if not available_bonus:
        await bot.send_message(chat_id, "❌ Бонусный блок недоступен")
        return
    
    questions = available_bonus.get("questions", [])
    
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
        await bot.send_message(chat_id, f"🎉 Бонусный блок завершён!\\nСчёт: {score}", reply_markup=kb)
        return
    
    question = questions[bonus_answer_cnt]
    options = question.get("options", {})
    
    text = f"🎁 *{available_bonus.get('title', 'Бонусный блок')}*\\n\\n"
    text += f"❓ *Вопрос {bonus_answer_cnt + 1} из {len(questions)}*\\n\\n"
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
content = content.replace('if __name__ == "__main__":', bonus_handlers + 'if __name__ == "__main__":')

# Добавляем кнопку бонусного блока в ask_question
bonus_button_addition = '''        # Проверяем доступность бонусного блока
        if bonus_blocks and not bonus_unlocked:
            for bonus_block in bonus_blocks:
                if score >= bonus_block.get("min_score", 0):
                    kb_buttons.append([KeyboardButton(text="🎁 Открыть бонусный блок")])
                    break
'''

content = content.replace(
    'kb_buttons.append([KeyboardButton(text="👤 Профиль")])',
    bonus_button_addition + '        kb_buttons.append([KeyboardButton(text="👤 Профиль")])'
)

# Записываем исправленный файл
with open('/home/bot/empire-bot/bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Бонусная функциональность добавлена корректно!")
