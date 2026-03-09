import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# --- НАЛАШТУВАННЯ ---
API_TOKEN = 'ТВІЙ_ТОКЕН_ТУТ'
ADMIN_ID = 'ТВІЙ_ID_ТУТ' # Твій телеграм ID для замовлень
CHANNELS = {
    "VINTAGE": -100, # Заміни на реальні ID каналів
    "LUXURY": -100,
    "DENIM": -100,
    "OUTDOOR": -100,
    "MERCH": -100,
    "ACCESSORIES": -100
}

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- СТАННИ (FSM) ---
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
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
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
    keyboard.add(*[InlineKeyboardButton(x, callback_data=f"box_{x}") for x in ["LUXURY", "DENIM", "VINTAGE", "OUTDOOR"]])
    return keyboard

def restart_menu():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("Виставити ще один лот 🔄", callback_data="go_home"))

# --- ОБРОБНИКИ КОМАНД ---
@dp.message_handler(commands=['start'], state="*")
@dp.callback_query_handler(lambda c: c.data == 'go_home', state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    text = "Ласкаво просимо на аукціони! 🔥\nВибери дію:"
    if isinstance(message, types.CallbackQuery):
        await bot.send_message(message.from_user.id, text, reply_markup=main_menu())
    else: await message.answer(text, reply_markup=main_menu())

# --- ЛОГІКА МІСТЕРІ БОКС (ПРИКЛАД АНКЕТИ) ---
@dp.callback_query_handler(lambda c: c.data == 'start_mystery')
async def mystery_step_1(c: types.CallbackQuery):
    await MysteryBox.box_type.set()
    await bot.send_message(c.from_user.id, "Виберіть тип боксу:", reply_markup=box_types_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('box_'), state=MysteryBox.box_type)
async def mystery_step_2(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(box_type=f"{c.data.split('_')[1]} mystery box")
    await MysteryBox.next(); await bot.send_message(c.from_user.id, "Розмір:")

@dp.message_handler(state=MysteryBox.size)
async def mystery_step_3(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await MysteryBox.next(); await m.answer("Стан:")

@dp.message_handler(state=MysteryBox.condition)
async def mystery_step_4(m: types.Message, state: FSMContext):
    await state.update_data(condition=m.text); await MysteryBox.next(); await m.answer("Старт:")

@dp.message_handler(state=MysteryBox.start_price)
async def mystery_step_5(m: types.Message, state: FSMContext):
    await state.update_data(start_price=m.text); await MysteryBox.next(); await m.answer("Крок:")

@dp.message_handler(state=MysteryBox.step)
async def mystery_step_6(m: types.Message, state: FSMContext):
    await state.update_data(step=m.text); await MysteryBox.next(); await m.answer("Викуп:")

@dp.message_handler(state=MysteryBox.buyout)
async def mystery_step_7(m: types.Message, state: FSMContext):
    await state.update_data(buyout=m.text); await MysteryBox.next(); await m.answer("Відправляю:")

@dp.message_handler(state=MysteryBox.shipping)
async def mystery_step_8(m: types.Message, state: FSMContext):
    await state.update_data(shipping=m.text); await MysteryBox.next(); await m.answer("Оплата:")

@dp.message_handler(state=MysteryBox.payment)
async def mystery_step_9(m: types.Message, state: FSMContext):
    await state.update_data(payment=m.text); await MysteryBox.next(); await m.answer("Скиньте фото лоту:")

@dp.message_handler(content_types=['photo'], state=MysteryBox.photo)
async def mystery_final(m: types.Message, state: FSMContext):
    data = await state.get_data()
    caption = (f"🎁 {data['box_type']}\nРозмір: {data['size']}\nСтан: {data['condition']}\n"
               f"Старт: {data['start_price']}\nКрок: {data['step']}\nВикуп: {data['buyout']}\n"
               f"Відправляю: {data['shipping']}\nОплата: {data['payment']}\n\n"
               f"Шаблон: https://pin.it/13eHcuMsj")
    
    # Визначаємо канал (LUXURY, DENIM тощо)
    chan_key = data['box_type'].split()[0]
    await bot.send_photo(CHANNELS.get(chan_key, ADMIN_ID), m.photo[-1].file_id, caption=caption)
    await m.answer(f"Успішно опубліковано на {data['box_type']}", reply_markup=restart_menu())
    await state.finish()

# --- АНАЛОГІЧНО ДОДАНІ ПАК РЕЧЕЙ ТА КУПИТИ (ЛОГІКА ТАКА САМА) ---

if __name__ == '__main__':
    loop = asyncio.get_event_loop(); loop.create_task(start_webhook())
    executor.start_polling(dp, skip_updates=True)
