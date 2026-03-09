import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryContextStorage

# --- НАЛАШТУВАННЯ ---
API_TOKEN = 'ТВІЙ_ТОКЕН_ТУТ'
ADMIN_ID = 'ТВІЙ_ID_ТУТ' # Сюди приходитимуть замовлення

bot = Bot(token=API_TOKEN)
storage = MemoryContextStorage()
dp = Dispatcher(bot, storage=storage)

# --- СТАННИ АНКЕТИ (FSM) ---
class BuyOrder(StatesGroup):
    channel = State()
    name = State()
    size = State()
    budget = State()
    delivery = State()
    payment = State()

# --- БЛОК ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_webhook():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- КЛАВІАТУРИ ---
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Виставити лот 📦", callback_data="start_listing"),
        InlineKeyboardButton("Купити 💸", callback_data="start_buying")
    )
    return keyboard

def channels_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    # Твої пабліки (можеш змінити назви)
    btns = [
        InlineKeyboardButton("VINTAGE", callback_data="chan_vintage"),
        InlineKeyboardButton("LUXURY", callback_data="chan_luxury"),
        InlineKeyboardButton("DENIM", callback_data="chan_denim"),
        InlineKeyboardButton("MERCH", callback_data="chan_merch")
    ]
    keyboard.add(*btns)
    return keyboard

def restart_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Виставити ще один лот 🔄", callback_data="start_listing"))
    return keyboard

# --- ОБРОБНИКИ КОМАНД ---

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "Ласкаво просимо на аукціони! 🔥\nВибери дію:",
        reply_markup=main_menu()
    )

# --- ЛОГІКА "КУПИТИ" (АНКЕТА) ---

@dp.callback_query_handler(lambda c: c.data == 'start_buying')
async def buy_step_1(callback_query: types.CallbackQuery):
    await BuyOrder.channel.set()
    await bot.send_message(callback_query.from_user.id, "Вибери паблік, у якому бачив лот:", reply_markup=channels_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('chan_'), state=BuyOrder.channel)
async def buy_step_2(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(channel=callback_query.data.split('_')[1].upper())
    await BuyOrder.next()
    await bot.send_message(callback_query.from_user.id, "Введіть назву лоту:")

@dp.message_handler(state=BuyOrder.name)
async def buy_step_3(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await BuyOrder.next()
    await message.answer("Введіть ваш розмір:")

@dp.message_handler(state=BuyOrder.size)
async def buy_step_4(message: types.Message, state: FSMContext):
    await state.update_data(size=message.text)
    await BuyOrder.next()
    await message.answer("Який ваш бюджет?")

@dp.message_handler(state=BuyOrder.budget)
async def buy_step_5(message: types.Message, state: FSMContext):
    await state.update_data(budget=message.text)
    await BuyOrder.next()
    await message.answer("Вкажіть дані для доставки (Місто, номер почти, ПІБ, телефон):")

@dp.message_handler(state=BuyOrder.delivery)
async def buy_step_6(message: types.Message, state: FSMContext):
    await state.update_data(delivery=message.text)
    await BuyOrder.next()
    await message.answer("Виберіть спосіб оплати (Карта, Накладений платіж тощо):")

@dp.message_handler(state=BuyOrder.payment)
async def buy_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    
    # Формуємо анкету для адміна
    order_text = (
        f"📩 Нове замовлення!\n\n"
        f"📍 Паблік: {data['channel']}\n"
        f"🏷 Назва: {data['name']}\n"
        f"📏 Розмір: {data['size']}\n"
        f"💰 Бюджет: {data['budget']}\n"
        f"🚚 Доставка: {data['delivery']}\n"
        f"💳 Оплата: {message.text}\n"
        f"👤 Покупець: @{message.from_user.username}"
    )
    
    await bot.send_message(ADMIN_ID, order_text)
    await message.answer("Ваша заявка прийнята! Адмін зв'яжеться з вами найближчим часом.")

# --- ЛОГІКА "ВИСТАВИТИ ЛОТ" ---

@dp.callback_query_handler(lambda c: c.data == 'start_listing')
async def start_listing(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Окей! Скидай фото та опис лоту.")

# Приклад фіналу публікації (БЕЗ смайлика)
# Коли твій код закінчить публікацію, виклич цей текст:
# await message.answer(f"Успішно опубліковано на {category}", reply_markup=restart_menu())

# --- ЗАПУСК ---
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_webhook())
    executor.start_polling(dp, skip_updates=True)
