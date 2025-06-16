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
