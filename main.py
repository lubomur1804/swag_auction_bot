# --- ЛОГІКА МІСТЕРІ БОКС (ОНОВЛЕНО) ---
@dp.callback_query_handler(lambda c: c.data == 'start_mystery')
async def myst_start(c: types.CallbackQuery):
    await MysteryBox.box_type.set()
    await bot.send_message(c.from_user.id, "📦 Виберіть категорію вашого Mystery Box:", reply_markup=box_types_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('box_'), state=MysteryBox.box_type)
async def myst_1(c: types.CallbackQuery, state: FSMContext):
    category = c.data.split('_')[1]
    await state.update_data(box_type=f"{category} MYSTERY BOX")
    await MysteryBox.next()
    await bot.send_message(c.from_user.id, "📏 Вкажіть розміри речей у боксі (наприклад, M-L або 42-44):")

@dp.message_handler(state=MysteryBox.size)
async def myst_2(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text)
    await MysteryBox.next()
    await m.answer("✨ Опишіть стан речей (наприклад, 10/10 або Нові):")

@dp.message_handler(state=MysteryBox.condition)
async def myst_3(m: types.Message, state: FSMContext):
    await state.update_data(condition=m.text)
    await MysteryBox.next()
    await m.answer("🏁 Стартова ціна (Старт):")

@dp.message_handler(state=MysteryBox.start_price)
async def myst_4(m: types.Message, state: FSMContext):
    await state.update_data(start_price=m.text)
    await MysteryBox.next()
    await m.answer("📈 Крок аукціону:")

@dp.message_handler(state=MysteryBox.step)
async def myst_5(m: types.Message, state: FSMContext):
    await state.update_data(step=m.text)
    await MysteryBox.next()
    await m.answer("💰 Ціна викупу (якщо немає — '-') :")

@dp.message_handler(state=MysteryBox.buyout)
async def myst_6(m: types.Message, state: FSMContext):
    await state.update_data(buyout=m.text)
    await MysteryBox.next()
    await m.answer("🚚 Способи доставки (Нова пошта / Укрпошта):")

@dp.message_handler(state=MysteryBox.shipping)
async def myst_7(m: types.Message, state: FSMContext):
    await state.update_data(shipping=m.text)
    await MysteryBox.next()
    await m.answer("💳 Варіанти оплати:")

@dp.message_handler(state=MysteryBox.payment)
async def myst_8(m: types.Message, state: FSMContext):
    await state.update_data(payment=m.text)
    await MysteryBox.next()
    await m.answer("📸 Надішліть круте фото для обкладинки боксу:")

@dp.message_handler(content_types=['photo'], state=MysteryBox.photo)
async def myst_final(m: types.Message, state: FSMContext):
    d = await state.get_data()
    # Оформлення в стилі твоїх кращих лотів
    cap = (
        f"❓ **{d['box_type']}** 📦\n\n"
        f"Розмір: {d['size']}\n"
        f"Стан: {d['condition']}\n\n"
        f"Старт: {d['start_price']}\n"
        f"Крок: {d['step']}\n"
        f"Викуп: {d['buyout']}\n\n"
        f"Відправляю: {d['shipping']}\n"
        f"Оплата: {d['payment']}\n\n"
        f"Продавець: @{m.from_user.username}\n"
        f"Приклад того, що може бути всередині: https://pin.it/13eHcuMsj"
    )
    # Визначаємо канал за типом боксу
    chan_key = d['box_type'].split()[0]
    target_channel = CHANNELS.get(chan_key, ADMIN_ID)
    
    await bot.send_photo(target_channel, m.photo[-1].file_id, caption=cap, parse_mode="Markdown")
    await m.answer(f"Ваш {d['box_type']} успішно виставлений! 🔥", reply_markup=restart_menu())
    await state.finish()
