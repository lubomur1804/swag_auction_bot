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

# --- 1. НАЛАШТУВАННЯ (Твої дані вже тут) ---
API_TOKEN = '8294128537:AAE8G3c23bhBqsqHTKjBcd7Oq-e6NhdjrVM'
ADMIN_ID = 5055318931
GEMINI_KEY = 'ВСТАВ_СВІЙ_КЛЮЧ_ТУТ' # Встав ключ, якщо маєш

CHANNELS = {
    "VINTAGE": -1002283307774, # Твої ID каналів
    "LUXURY": -1002283307774,
    "DENIM": -1002283307774,
    "OUTDOOR": -1002283307774,
    "MERCH": -1002283307774,
    "ACCESSORIES": -1002283307774
}

# --- 2. ІНІЦІАЛІЗАЦІЯ (Щоб не було помилки NameError) ---
logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- 3. СТАНИ (FSM) ---
class BuyOrder(StatesGroup):
    channel = State(); name = State(); size = State(); budget = State(); delivery = State(); payment = State()

class PackOrder(StatesGroup):
    details = State(); size = State(); condition = State(); start_price = State(); step = State(); buyout = State(); shipping = State(); payment = State(); photo = State()

class MysteryBox(StatesGroup):
    box_type = State(); size = State(); condition = State(); start_price = State(); step = State(); buyout = State(); shipping = State(); payment = State(); photo = State()

# --- 4. КЛАВІАТУРИ ---
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Виставити лот 📦", callback_data="start_listing"),
        InlineKeyboardButton("Пак речей 🧺", callback_data="start_pack"),
        InlineKeyboardButton("Містері Бокс 🎁", callback_data="start_mystery"),
        InlineKeyboardButton("Купити 💸", callback_data="start_buying")
    )
    return keyboard

def box_types_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    for x in ["LUXURY", "DENIM", "VINTAGE", "OUTDOOR"]:
        keyboard.insert(InlineKeyboardButton(x, callback_data=f"box_{x}"))
    return keyboard

def restart_menu():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("Повернутись в меню 🔄", callback_data="go_home"))

# --- 5. ОБРОБНИКИ (ЛОГІКА) ---

@dp.message_handler(commands=['start'], state="*")
@dp.callback_query_handler(lambda c: c.data == 'go_home', state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    text = "Ласкаво просимо на аукціони! 🔥\nВибери дію:"
    if isinstance(message, types.CallbackQuery):
        await bot.send_message(message.from_user.id, text, reply_markup=main_menu())
    else:
        await message.answer(text, reply_markup=main_menu())

# ЛОГІКА ПАК РЕЧЕЙ
@dp.callback_query_handler(lambda c: c.data == 'start_pack')
async def pack_start(c: types.CallbackQuery):
    await PackOrder.details.set()
    await bot.send_message(c.from_user.id, "🧺 Введіть назву та деталі паку:")

@dp.message_handler(state=PackOrder.details)
async def pack_1(m: types.Message, state: FSMContext):
    await state.update_data(details=m.text); await PackOrder.next(); await m.answer("📏 Введіть розміри:")

@dp.message_handler(state=PackOrder.size)
async def pack_2(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await PackOrder.next(); await m.answer("✨ Стан (напр. 10/10):")

@dp.message_handler(state=PackOrder.condition)
async def pack_3(m: types.Message, state: FSMContext):
    await state.update_data(condition=m.text); await PackOrder.next(); await m.answer("🏁 Старт:")

@dp.message_handler(state=PackOrder.start_price)
async def pack_4(m: types.Message, state: FSMContext):
    await state.update_data(start_price=m.text); await PackOrder.next(); await m.answer("📈 Крок:")

@dp.message_handler(state=PackOrder.step)
async def pack_5(m: types.Message, state: FSMContext):
    await state.update_data(step=m.text); await PackOrder.next(); await m.answer("💰 Викуп (якщо немає '-'):")

@dp.message_handler(state=PackOrder.buyout)
async def pack_6(m: types.Message, state: FSMContext):
    await state.update_data(buyout=m.text); await PackOrder.next(); await m.answer("🚚 Відправляю:")

@dp.message_handler(state=PackOrder.shipping)
async def pack_7(m: types.Message, state: FSMContext):
    await state.update_data(shipping=m.text); await PackOrder.next(); await m.answer("💳 Оплата:")

@dp.message_handler(state=PackOrder.payment)
async def pack_8(m: types.Message, state: FSMContext):
    await state.update_data(payment=m.text); await PackOrder.next(); await m.answer("📸 Надішліть фото паку:")

@dp.message_handler(content_types=['photo'], state=PackOrder.photo)
async def pack_final(m: types.Message, state: FSMContext):
    d = await state.get_data()
    cap = (f"🧺 **ПАК РЕЧЕЙ**\n\nНазва: {d['details']}\n\nРозмір: {d['size']}\nСтан: {d['condition']}\n\n"
           f"Старт: {d['start_price']}\nКрок: {d['step']}\nВикуп: {d['buyout']}\n\n"
           f"Відправляю: {d['shipping']}\nОплата: {d['payment']}\n\nПродавець: @{m.from_user.username}\n"
           f"Кінець через 24 години після останньої ставки.")
    await bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=cap, parse_mode="Markdown")
    await m.answer("Успішно опубліковано на ПАК РЕЧЕЙ!", reply_markup=restart_menu())
    await state.finish()

# ЛОГІКА МІСТЕРІ БОКС
@dp.callback_query_handler(lambda c: c.data == 'start_mystery')
async def myst_start(c: types.CallbackQuery):
    await MysteryBox.box_type.set()
    await bot.send_message(c.from_user.id, "📦 Виберіть тип боксу:", reply_markup=box_types_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('box_'), state=MysteryBox.box_type)
async def myst_1(c: types.CallbackQuery, state: FSMContext):
    type_box = c.data.split('_')[1]
    await state.update_data(box_type=f"{type_box} MYSTERY BOX")
    await MysteryBox.next(); await bot.send_message(c.from_user.id, "📏 Розміри речей:")

@dp.message_handler(state=MysteryBox.size)
async def myst_2(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await MysteryBox.next(); await m.answer("✨ Стан:")

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
    await state.update_data(buyout=m.text); await MysteryBox.next(); await m.answer("🚚 Відправляю:")

@dp.message_handler(state=MysteryBox.shipping)
async def myst_7(m: types.Message, state: FSMContext):
    await state.update_data(shipping=m.text); await MysteryBox.next(); await m.answer("💳 Оплата:")

@dp.message_handler(state=MysteryBox.payment)
async def myst_8(m: types.Message, state: FSMContext):
    await state.update_data(payment=m.text); await MysteryBox.next(); await m.answer("📸 Надішліть фото боксу:")

@dp.message_handler(content_types=['photo'], state=MysteryBox.photo)
async def myst_final(m: types.Message, state: FSMContext):
    d = await state.get_data()
    cap = (f"❓ **{d['box_type']}** 📦\n\nРозмір: {d['size']}\nСтан: {d['condition']}\n\n"
           f"Старт: {d['start_price']}\nКрок: {d['step']}\nВикуп: {d['buyout']}\n\n"
           f"Відправляю: {d['shipping']}\nОплата: {d['payment']}\n\nПродавець: @{m.from_user.username}\n"
           f"Приклад: https://pin.it/13eHcuMsj")
    chan = CHANNELS.get(d['box_type'].split()[0], ADMIN_ID)
    await bot.send_photo(chan, m.photo[-1].file_id, caption=cap, parse_mode="Markdown")
    await m.answer(f"Успішно опубліковано на {d['box_type']}", reply_markup=restart_menu())
    await state.finish()

# ЛОГІКА КУПИТИ
@dp.callback_query_handler(lambda c: c.data == 'start_buying')
async def buy_start(c: types.CallbackQuery):
    await BuyOrder.channel.set()
    kb = InlineKeyboardMarkup(row_width=2)
    for x in CHANNELS.keys(): kb.insert(InlineKeyboardButton(x, callback_data=f"buychan_{x}"))
    await bot.send_message(c.from_user.id, "Вибери паблік:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('buychan_'), state=BuyOrder.channel)
async def buy_1(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(channel=c.data.split('_')[1]); await BuyOrder.next(); await bot.send_message(c.from_user.id, "Назва лоту:")

@dp.message_handler(state=BuyOrder.name)
async def buy_2(m: types.Message, state: FSMContext):
    await state.update_data(name=m.text); await BuyOrder.next(); await m.answer("Ваш розмір:")

@dp.message_handler(state=BuyOrder.size)
async def buy_3(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await BuyOrder.next(); await m.answer("Ваш бюджет:")

@dp.message_handler(state=BuyOrder.budget)
async def buy_4(m: types.Message, state: FSMContext):
    await state.update_data(budget=m.text); await BuyOrder.next(); await m.answer("Дані доставки (ПІБ, Пошта, Тел):")

@dp.message_handler(state=BuyOrder.delivery)
async def buy_5(m: types.Message, state: FSMContext):
    await state.update_data(delivery=m.text); await BuyOrder.next(); await m.answer("Оплата:")

@dp.message_handler(state=BuyOrder.payment)
async def buy_final(m: types.Message, state: FSMContext):
    d = await state.get_data()
    res = (f"📩 **НОВЕ ЗАМОВЛЕННЯ**\n\n📍 Канал: {d['channel']}\n🏷 Назва: {d['name']}\n📏 Розмір: {d['size']}\n"
           f"💰 Бюджет: {d['budget']}\n🚚 Доставка: {d['delivery']}\n💳 Оплата: {m.text}\n👤 Покупець: @{m.from_user.username}")
    await bot.send_message(ADMIN_ID, res, parse_mode="Markdown")
    await m.answer("Заявку надіслано!", reply_markup=restart_menu())
    await state.finish()

# ЛОГІКА СТАНДАРТНИЙ ЛОТ
@dp.callback_query_handler(lambda c: c.data == 'start_listing')
async def list_start(c: types.CallbackQuery):
    await bot.send_message(c.from_user.id, "Надсилай фото з описом одним повідомленням!")

@dp.message_handler(content_types=['photo'])
async def handle_std_lot(m: types.Message):
    if not m.caption: return await m.answer("Додай опис до фото!")
    prompt = f"Визнач категорію одним словом (MERCH, VINTAGE, LUXURY, DENIM, ACCESSORIES, OUTDOOR): {m.caption}."
    try:
        resp = model.generate_content(prompt).text.strip().upper()
    except:
        resp = "ACCESSORIES"
    chan = CHANNELS.get(resp, ADMIN_ID)
    await bot.send_photo(chan, m.photo[-1].file_id, caption=m.caption)
    await m.answer(f"Успішно опубліковано на {resp}", reply_markup=restart_menu())

# ВЕБ-СЕРВЕР (Для Render)
async def handle(request): return web.Response(text="Bot is running!")
async def start_webhook():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_webhook())
    executor.start_polling(dp, skip_updates=True)
