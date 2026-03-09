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

# --- НАЛАШТУВАННЯ (ТВОЇ ДАНІ ВЖЕ ТУТ) ---
API_TOKEN = '8294128537:AAE8G3c23bhBqsqHTKjBcd7Oq-e6NhdjrVM'
ADMIN_ID = 5055318931  # Твій ID зафіксовано
GEMINI_KEY = 'ВСТАВ_СВІЙ_GEMINI_KEY_ТУТ' # Єдине, що треба вставити

# ID КАНАЛІВ (Заміни на реальні ID -100...)
CHANNELS = {
    "VINTAGE": -100,
    "LUXURY": -100,
    "DENIM": -100,
    "OUTDOOR": -100,
    "MERCH": -100,
    "ACCESSORIES": -100
}

logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- СТАНИ (FSM) ---
class BuyOrder(StatesGroup):
    channel = State(); name = State(); size = State(); budget = State(); delivery = State(); payment = State()

class PackOrder(StatesGroup):
    details = State(); size = State(); start_price = State(); step = State(); buyout = State(); shipping = State(); payment = State(); photo = State()

class MysteryBox(StatesGroup):
    box_type = State(); size = State(); condition = State(); start_price = State(); step = State(); buyout = State(); shipping = State(); payment = State(); photo = State()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request): return web.Response(text="Bot is running!")
async def start_webhook():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- КЛАВІАТУРИ ---
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
    return InlineKeyboardMarkup().add(InlineKeyboardButton("Виставити ще один лот 🔄", callback_data="go_home"))

# --- ОБРОБНИКИ ---
@dp.message_handler(commands=['start'], state="*")
@dp.callback_query_handler(lambda c: c.data == 'go_home', state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    text = "Ласкаво просимо на аукціони! 🔥\nВибери дію:"
    if isinstance(message, types.CallbackQuery):
        await bot.send_message(message.from_user.id, text, reply_markup=main_menu())
    else:
        await message.answer(text, reply_markup=main_menu())

# --- КУПИТИ (АНКЕТА) ---
@dp.callback_query_handler(lambda c: c.data == 'start_buying')
async def buy_start(c: types.CallbackQuery):
    await BuyOrder.channel.set()
    kb = InlineKeyboardMarkup(row_width=2)
    for x in CHANNELS.keys():
        kb.insert(InlineKeyboardButton(x, callback_data=f"buychan_{x}"))
    await bot.send_message(c.from_user.id, "Вибери паблік, у якому бачив лот:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('buychan_'), state=BuyOrder.channel)
async def buy_1(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(channel=c.data.split('_')[1])
    await BuyOrder.next(); await bot.send_message(c.from_user.id, "Введіть назву лоту:")

@dp.message_handler(state=BuyOrder.name)
async def buy_2(m: types.Message, state: FSMContext):
    await state.update_data(name=m.text); await BuyOrder.next(); await m.answer("Введіть розмір:")

@dp.message_handler(state=BuyOrder.size)
async def buy_3(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await BuyOrder.next(); await m.answer("Бюджет:")

@dp.message_handler(state=BuyOrder.budget)
async def buy_4(m: types.Message, state: FSMContext):
    await state.update_data(budget=m.text); await BuyOrder.next(); await m.answer("Дані для доставки (ПІБ, Місто, Пошта, Тел):")

@dp.message_handler(state=BuyOrder.delivery)
async def buy_5(m: types.Message, state: FSMContext):
    await state.update_data(delivery=m.text); await BuyOrder.next(); await m.answer("Спосіб оплати:")

@dp.message_handler(state=BuyOrder.payment)
async def buy_final(m: types.Message, state: FSMContext):
    d = await state.get_data()
    res = (f"📩 ЗАМОВЛЕННЯ\nКанал: {d['channel']}\nЛот: {d['name']}\nРозмір: {d['size']}\n"
           f"Бюджет: {d['budget']}\nДоставка: {d['delivery']}\nОплата: {m.text}\nЮзер: @{m.from_user.username}")
    await bot.send_message(ADMIN_ID, res)
    await m.answer("Заявку надіслано!", reply_markup=restart_menu())
    await state.finish()

# --- МІСТЕРІ БОКС ---
@dp.callback_query_handler(lambda c: c.data == 'start_mystery')
async def myst_start(c: types.CallbackQuery):
    await MysteryBox.box_type.set()
    await bot.send_message(c.from_user.id, "Виберіть тип боксу:", reply_markup=box_types_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('box_'), state=MysteryBox.box_type)
async def myst_1(c: types.CallbackQuery, state: FSMContext):
    type_box = c.data.split('_')[1]
    await state.update_data(box_type=f"{type_box} mystery box")
    await MysteryBox.next(); await bot.send_message(c.from_user.id, "Вкажіть розмір:")

@dp.message_handler(state=MysteryBox.size)
async def myst_2(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await MysteryBox.next(); await m.answer("Стан:")

@dp.message_handler(state=MysteryBox.condition)
async def myst_3(m: types.Message, state: FSMContext):
    await state.update_data(condition=m.text); await MysteryBox.next(); await m.answer("Старт:")

@dp.message_handler(state=MysteryBox.start_price)
async def myst_4(m: types.Message, state: FSMContext):
    await state.update_data(start_price=m.text); await MysteryBox.next(); await m.answer("Крок:")

@dp.message_handler(state=MysteryBox.step)
async def myst_5(m: types.Message, state: FSMContext):
    await state.update_data(step=m.text); await MysteryBox.next(); await m.answer("Викуп:")

@dp.message_handler(state=MysteryBox.buyout)
async def myst_6(m: types.Message, state: FSMContext):
    await state.update_data(buyout=m.text); await MysteryBox.next(); await m.answer("Відправляю:")

@dp.message_handler(state=MysteryBox.shipping)
async def myst_7(m: types.Message, state: FSMContext):
    await state.update_data(shipping=m.text); await MysteryBox.next(); await m.answer("Оплата:")

@dp.message_handler(state=MysteryBox.payment)
async def myst_8(m: types.Message, state: FSMContext):
    await state.update_data(payment=m.text); await MysteryBox.next(); await m.answer("Надішліть фото лоту:")

@dp.message_handler(content_types=['photo'], state=MysteryBox.photo)
async def myst_final(m: types.Message, state: FSMContext):
    d = await state.get_data()
    cap = (f"🎁 {d['box_type']}\n📏 Розмір: {d['size']}\n✨ Стан: {d['condition']}\n🏁 Старт: {d['start_price']}\n"
           f"📈 Крок: {d['step']}\n💰 Викуп: {d['buyout']}\n🚚 Відправляю: {d['shipping']}\n💳 Оплата: {d['payment']}\n\n"
           f"Шаблон: https://pin.it/13eHcuMsj")
    chan = d['box_type'].split()[0]
    await bot.send_photo(CHANNELS.get(chan, ADMIN_ID), m.photo[-1].file_id, caption=cap)
    await m.answer(f"Успішно опубліковано на {d['box_type']}", reply_markup=restart_menu())
    await state.finish()

# --- ПАК РЕЧЕЙ ---
@dp.callback_query_handler(lambda c: c.data == 'start_pack')
async def pack_start(c: types.CallbackQuery):
    await PackOrder.details.set(); await bot.send_message(c.from_user.id, "Пак речей (річ, бренд):")

@dp.message_handler(state=PackOrder.details)
async def pack_1(m: types.Message, state: FSMContext):
    await state.update_data(details=m.text); await PackOrder.next(); await m.answer("Розмір:")

@dp.message_handler(state=PackOrder.size)
async def pack_2(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await PackOrder.next(); await m.answer("Старт:")

@dp.message_handler(state=PackOrder.start_price)
async def pack_3(m: types.Message, state: FSMContext):
    await state.update_data(start_price=m.text); await PackOrder.next(); await m.answer("Крок:")

@dp.message_handler(state=PackOrder.step)
async def pack_4(m: types.Message, state: FSMContext):
    await state.update_data(step=m.text); await PackOrder.next(); await m.answer("Викуп:")

@dp.message_handler(state=PackOrder.buyout)
async def pack_5(m: types.Message, state: FSMContext):
    await state.update_data(buyout=m.text); await PackOrder.next(); await m.answer("Відправляю:")

@dp.message_handler(state=PackOrder.shipping)
async def pack_6(m: types.Message, state: FSMContext):
    await state.update_data(shipping=m.text); await PackOrder.next(); await m.answer("Оплата:")

@dp.message_handler(state=PackOrder.payment)
async def pack_7(m: types.Message, state: FSMContext):
    await state.update_data(payment=m.text); await PackOrder.next(); await m.answer("Скиньте фото паку:")

@dp.message_handler(content_types=['photo'], state=PackOrder.photo)
async def pack_final(m: types.Message, state: FSMContext):
    d = await state.get_data()
    cap = (f"🧺 ПАК РЕЧЕЙ\n📦 Деталі: {d['details']}\n📏 Розмір: {d['size']}\n🏁 Старт: {d['start_price']}\n"
           f"📈 Крок: {d['step']}\n💰 Викуп: {d['buyout']}\n🚚 Відправляю: {d['shipping']}\n💳 Оплата: {d['payment']}")
    await bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=cap)
    await m.answer("Успішно опубліковано на ПАК РЕЧЕЙ", reply_markup=restart_menu())
    await state.finish()

# --- СТАНДАРТНИЙ ЛОТ (GEMINI) ---
@dp.callback_query_handler(lambda c: c.data == 'start_listing')
async def list_start(c: types.CallbackQuery):
    await bot.send_message(c.from_user.id, "Надсилай фото з описом!")

@dp.message_handler(content_types=['photo'])
async def handle_std_lot(m: types.Message):
    if not m.caption: return await m.answer("Додай опис до фото!")
    prompt = f"Визнач категорію одним словом (MERCH, VINTAGE, LUXURY, DENIM, ACCESSORIES, OUTDOOR): {m.caption}."
    resp = model.generate_content(prompt).text.strip().upper()
    chan = CHANNELS.get(resp, ADMIN_ID)
    await bot.send_photo(chan, m.photo[-1].file_id, caption=m.caption)
    await m.answer(f"Успішно опубліковано на {resp}", reply_markup=restart_menu())

if __name__ == '__main__':
    loop = asyncio.get_event_loop(); loop.create_task(start_webhook())
    executor.start_polling(dp, skip_updates=True)
