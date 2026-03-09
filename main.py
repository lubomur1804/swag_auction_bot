import os
import asyncio
import logging
import google.generativeai as genai
from aiohttp import web
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# --- НАЛАШТУВАННЯ ---
API_TOKEN = '8294128537:AAE8G3c23bhBqsqHTKjBcd7Oq-e6NhdjrVM'
ADMIN_ID = 5055318931
GEMINI_KEY = 'ВСТАВ_СВІЙ_КЛЮЧ'

# Посилання на твоє фото для Містері Боксу
MYSTERY_BOX_PHOTO = "https://i.ibb.co/6R0yX0P/mystery-box.jpg" 

CHANNELS = {
    "VINTAGE": -1002283307774,
    "LUXURY": -1002283307774,
    "DENIM": -1002283307774,
    "OUTDOOR": -1002283307774,
    "MERCH": -1002283307774,
    "ACCESSORIES": -1002283307774
}

logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- СТАНИ ---
class PackOrder(StatesGroup):
    title = State(); size = State(); condition = State(); start_price = State(); step = State(); buyout = State(); shipping = State(); payment = State(); photo = State()

class MysteryBox(StatesGroup):
    box_type = State(); size = State(); condition = State(); start_price = State(); step = State(); buyout = State(); shipping = State(); payment = State()

# --- МЕНЮ ---
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Виставити лот 📦", callback_data="start_listing"),
        InlineKeyboardButton("Пак речей 🧺", callback_data="start_pack"),
        InlineKeyboardButton("Містері Бокс 🎁", callback_data="start_mystery")
    )
    return keyboard

def box_types_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    for x in ["LUXURY", "DENIM", "VINTAGE", "OUTDOOR"]:
        keyboard.insert(InlineKeyboardButton(x, callback_data=f"box_{x}"))
    return keyboard

@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Вибери дію, бро:", reply_markup=main_menu())

# --- 🧺 ЛОГІКА ПАК РЕЧЕЙ (З ФОТО) ---
@dp.callback_query_handler(lambda c: c.data == 'start_pack')
async def pack_start(c: types.CallbackQuery):
    await PackOrder.title.set(); await bot.send_message(c.from_user.id, "🧺 Назва паку:")

@dp.message_handler(state=PackOrder.title)
async def pack_1(m: types.Message, state: FSMContext):
    await state.update_data(title=m.text); await PackOrder.next(); await m.answer("📏 Розмір:")

@dp.message_handler(state=PackOrder.size)
async def pack_2(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await PackOrder.next(); await m.answer("✨ Стан:")

@dp.message_handler(state=PackOrder.condition)
async def pack_3(m: types.Message, state: FSMContext):
    await state.update_data(condition=m.text); await PackOrder.next(); await m.answer("🏁 Старт:")

@dp.message_handler(state=PackOrder.start_price)
async def pack_4(m: types.Message, state: FSMContext):
    await state.update_data(start_price=m.text); await PackOrder.next(); await m.answer("📈 Крок:")

@dp.message_handler(state=PackOrder.step)
async def pack_5(m: types.Message, state: FSMContext):
    await state.update_data(step=m.text); await PackOrder.next(); await m.answer("💰 Викуп:")

@dp.message_handler(state=PackOrder.buyout)
async def pack_6(m: types.Message, state: FSMContext):
    await state.update_data(buyout=m.text); await PackOrder.next(); await m.answer("🚚 Відправка:")

@dp.message_handler(state=PackOrder.shipping)
async def pack_7(m: types.Message, state: FSMContext):
    await state.update_data(shipping=m.text); await PackOrder.next(); await m.answer("💳 Оплата:")

@dp.message_handler(state=PackOrder.payment)
async def pack_8(m: types.Message, state: FSMContext):
    await state.update_data(payment=m.text); await PackOrder.next(); await m.answer("📸 Фото паку:")

@dp.message_handler(content_types=['photo'], state=PackOrder.photo)
async def pack_final(m: types.Message, state: FSMContext):
    d = await state.get_data()
    cap = (f"🧺 **ПАК РЕЧЕЙ**\n\nНазва: {d['title']}\n\nРозмір: {d['size']}\nСтан: {d['condition']}\n\n"
           f"Старт: {d['start_price']}\nКрок: {d['step']}\nВикуп: {d['buyout']}\n\n"
           f"Відправляю: {d['shipping']}\nОплата: {d['payment']}\n\nПродавець: @{m.from_user.username}")
    await bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=cap, parse_mode="Markdown")
    await m.answer("Пак надіслано! ✅"); await state.finish()

# --- 🎁 ЛОГІКА МІСТЕРІ БОКС (БЕЗ ЗАПИТУ ФОТО) ---
@dp.callback_query_handler(lambda c: c.data == 'start_mystery')
async def myst_start(c: types.CallbackQuery):
    await MysteryBox.box_type.set(); await bot.send_message(c.from_user.id, "📦 Оберіть категорію боксу:", reply_markup=box_types_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('box_'), state=MysteryBox.box_type)
async def myst_1(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(box_type=f"{c.data.split('_')[1]} MYSTERY BOX")
    await MysteryBox.next(); await bot.send_message(c.from_user.id, "📏 Розмір речей в боксі:")

@dp.message_handler(state=MysteryBox.size)
async def myst_2(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await MysteryBox.next(); await m.answer("✨ Стан речей:")

@dp.message_handler(state=MysteryBox.condition)
async def myst_3(m: types.Message, state: FSMContext):
    await state.update_data(condition=m.text); await MysteryBox.next(); await m.answer("🏁 Старт:")

@dp.message_handler(state=MysteryBox.start_price)
async def myst_4(m: types.Message, state: FSMContext):
    await state.update_data(start_price=m.text); await MysteryBox.next(); await m.answer("📈 Крок:")

@dp.message_handler(state=MysteryBox.step)
async def myst_5(m: types.Message, state: FSMContext):
    await state.update_data(step=m.text); await MysteryBox.next(); await m.answer("💰 Викуп:")

@dp.message_handler(state=MysteryBox.buyout)
async def myst_6(m: types.Message, state: FSMContext):
    await state.update_data(buyout=m.text); await MysteryBox.next(); await m.answer("🚚 Відправка:")

@dp.message_handler(state=MysteryBox.shipping)
async def myst_7(m: types.Message, state: FSMContext):
    await state.update_data(shipping=m.text); await MysteryBox.next(); await m.answer("💳 Оплата:")

@dp.message_handler(state=MysteryBox.payment)
async def myst_final(m: types.Message, state: FSMContext):
    d = await state.get_data()
    cap = (f"❓ **{d['box_type']}** 📦\n\nРозмір: {d['size']}\nСтан: {d['condition']}\n\n"
           f"Старт: {d['start_price']}\nКрок: {d['step']}\nВикуп: {d['buyout']}\n\n"
           f"Відправляю: {d['shipping']}\nОплата: {m.text}\n\nПродавець: @{m.from_user.username}\n"
           f"Приклад: https://pin.it/13eHcuMsj")
    
    chan = CHANNELS.get(d['box_type'].split()[0], ADMIN_ID)
    # ТУТ МАГІЯ: Бот сам шле твоє фото по лінку
    await bot.send_photo(chan, MYSTERY_BOX_PHOTO, caption=cap, parse_mode="Markdown")
    await m.answer(f"Бокс успішно виставлено! ✅"); await state.finish()

# --- СТАНДАРТНИЙ ЛОТ ---
@dp.message_handler(content_types=['photo'])
async def handle_std_lot(m: types.Message):
    if not m.caption: return await m.answer("Додай опис!")
    prompt = f"Визнач категорію одним словом: {m.caption}."
    try: resp = model.generate_content(prompt).text.strip().upper()
    except: resp = "VINTAGE"
    await bot.send_photo(CHANNELS.get(resp, ADMIN_ID), m.photo[-1].file_id, caption=m.caption)
    await m.answer(f"Опубліковано в {resp}! ✅")

# ВЕБ-СЕРВЕР
async def handle(request): return web.Response(text="Bot is running!")
async def start_webhook():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()

if __name__ == '__main__':
    loop = asyncio.get_event_loop(); loop.create_task(start_webhook())
    executor.start_polling(dp, skip_updates=True)
