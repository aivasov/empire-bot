# Читаем файл бота
with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим место после "Блок завершён!" где должны быть кнопки
# Ищем функцию ask_question и исправляем логику в конце

# Заменяем логику завершения блока
old_pattern = '''        await m.answer(f"🎉 Блок завершён! Ваш счёт: {score} баллов")
        return'''

new_pattern = '''        # Показываем кнопки после завершения блока
        kb_buttons = []
        
        # Проверяем доступность бонусного блока
        if bonus_blocks and not bonus_unlocked:
            for bonus_block in bonus_blocks:
                if score >= bonus_block.get("min_score", 0):
                    kb_buttons.append([KeyboardButton(text="🎁 Открыть бонусный блок")])
                    break
        
        # Если это последний блок, показываем финальные кнопки
        if block_idx >= len(blocks) - 1:
            btns = block.get("buttons", {})
            if btns.get("gift"):
                kb_buttons.append([KeyboardButton(text="🎁 Подарок")])
            if btns.get("site"):
                kb_buttons.append([KeyboardButton(text="🌐 Сайт")])
            if btns.get("contacts"):
                kb_buttons.append([KeyboardButton(text="📞 Контакты")])
        else:
            kb_buttons.append([KeyboardButton(text="Следующий блок")])
            
        kb_buttons.append([KeyboardButton(text="👤 Профиль")])
        
        kb = ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True)
        await m.answer(f"🎉 Блок завершён! Ваш счёт: {score} баллов\\nВыберите действие:", reply_markup=kb)
        return'''

content = content.replace(old_pattern, new_pattern)

# Сохраняем
with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Логика кнопок исправлена!")
