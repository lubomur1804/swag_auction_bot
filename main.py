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

# --- НАЛАШТУВАННЯ (Впиши свої дані) ---
API_TOKEN = '8294128537:AAE8G3c23bhBqsqHTKjBcd7Oq-e6NhdjrVM'
GEMINI_KEY = 'ВСТАВ_СВІЙ_КЛЮЧ_GEMINI'
ADMIN_ID = 5055318931
MYSTERY_BOX_URL = "https://i.ibb.co/6R0yX0P/mystery-box.jpg"

# ID Твоїх каналів (можеш змінити на різні, якщо треба)
CHANNELS = {
    "VINTAGE": -1002283307774,
    "LUXURY": -1002283307774,
    "DENIM": -1002283307774,
    "OUTDOOR": -1002283307774,
    "MERCH": -1002283307774,
    "ACCESSORIES": -1002283307774
}

# --- ІНІЦІАЛІЗАЦІЯ ---
logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class OrderState(StatesGroup):
    mode = State()
    title = State()
    size = State()
    condition = State()
    price_info = State()
    step = State()
    buyout = State()
    delivery = State()
    payment = State()
    photo = State()

# --- КНОПКИ ПІД ПОСТОМ ---
def post_keyboard():
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("ВИСТАВИТИ ЛОТ", url="https://t.me/swag_auction_bot"),
        InlineKeyboardButton("ПРАВИЛА", url="https://t.me/swagplabyla"),
        InlineKeyboardButton("ГАРАНТ", url="https://t.me/swagking61")
    )
    return kb

def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("Виставити лот 📦", callback_data="set_LOT"),
        InlineKeyboardButton("Купити 💸", callback_data="set_BUY"),
        InlineKeyboardButton("Містері Бокс 🎁", callback_data="set_BOX"),
        InlineKeyboardButton("Пак речей 🧺", callback_data="set_PACK")
    )
    return kb

# --- ОБРОБНИКИ ---
@dp.message_handler(commands=['start'], state="*")
async def cmd_start(m: types.Message, state: FSMContext):
    await state.finish()
    await m.answer("Ласкаво просимо на аукціони! 🔥\nВибери дію:", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data.startswith('set_'), state="*")
async def start_flow(c: types.CallbackQuery, state: FSMContext):
    mode = c.data.split('_')[1]
    await state.update_data(mode=mode)
    await OrderState.title.set()
    prompts = {"LOT": "Назва речі:", "BUY": "Що хочете купити?:", "BOX": "Категорія боксу:", "PACK": "Назва паку:"}
    await bot.send_message(c.from_user.id, prompts[mode])

@dp.message_handler(state=OrderState.title)
async def st_title(m: types.Message, state: FSMContext):
    await state.update_data(title=m.text); await OrderState.size.set(); await m.answer("Розмір:")

@dp.message_handler(state=OrderState.size)
async def st_size(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await OrderState.condition.set(); await m.answer("Стан:")

@dp.message_handler(state=OrderState.condition)
async def st_cond(m: types.Message, state: FSMContext):
    await state.update_data(condition=m.text); await OrderState.price_info.set()
    d = await state.get_data()
    await m.answer("Бюджет:" if d['mode'] == "BUY" else "Старт:")

@dp.message_handler(state=OrderState.price_info)
async def st_price(m: types.Message, state: FSMContext):
    await state.update_data(price=m.text)
    d = await state.get_data()
    if d['mode'] == "BUY": await OrderState.delivery.set(); await m.answer("Відправлення (місто/пошта):")
    else: await OrderState.step.set(); await m.answer("Крок:")

@dp.message_handler(state=OrderState.step)
async def st_step(m: types.Message, state: FSMContext):
    await state.update_data(step=m.text); await OrderState.buyout.set(); await m.answer("Викуп:")

@dp.message_handler(state=OrderState.buyout)
async def st_buyout(m: types.Message, state: FSMContext):
    await state.update_data(buyout=m.text); await OrderState.delivery.set(); await m.answer("Відправляю:")

@dp.message_handler(state=OrderState.delivery)
async def st_delivery(m: types.Message, state: FSMContext):
    await state.update_data(delivery=m.text); await OrderState.payment.set(); await m.answer("Оплата:")

@dp.message_handler(state=OrderState.payment)
async def st_payment(m: types.Message, state: FSMContext):
    await state.update_data(payment=m.text)
    d = await state.get_data()
    if d['mode'] in ["BOX", "BUY"]: await finish_order(m, state)
    else: await OrderState.photo.set(); await m.answer("📸 Надішліть фото лота:")

@dp.message_handler(content_types=['photo'], state=OrderState.photo)
async def st_photo(m: types.Message, state: FSMContext):
    await state.update_data(photo_id=m.photo[-1].file_id)
    await finish_order(m, state)

async def finish_order(m: types.Message, state: FSMContext):
    d = await state.get_data()
    user = f"@{m.from_user.username}" if m.from_user.username else "@swagking61"

    # --- ШІ АНАЛІЗ ТА ФОРМУВАННЯ ПОСТА ---
    prompt = f"""
    Ти адмін аукціону. Твоє завдання:
    1. Визначити категорію речі '{d['title']}' (VINTAGE, LUXURY, DENIM, OUTDOOR, MERCH, ACCESSORIES).
    2. Сформувати пост СУВОРО за шаблоном:
    
    Для ЛОТУ/ПАКУ/БОКСУ:
    Назва: {d['title']}
    Розмір: {d['size']}
    Стан: {d['condition']}
    Старт: {d.get('price', '')}
    Крок: {d.get('step', '')}
    Викуп: {d.get('buyout', '')}
    Відправляю: {d.get('delivery', '')}
    Оплата: {d['payment']}
    Продавець - {user}
    Кінець через 24 години після останньої ставки.
    
    Для КУПИТИ:
    Куплю: {d['title']}
    Розмір: {d['size']}
    Стан: {d['condition']}
    Бюджет: {d.get('price', '')}
    Відправлення: {d.get('delivery', '')}
    Оплачую: {d['payment']}
    Покупець - {user}
    
    Відповідь дай у форматі: КАТЕГОРІЯ ||| ТЕКСТ_ПОСТА
    """
    
    try:
        raw_res = ai_model.generate_content(prompt).text.split("|||")
        category = raw_res[0].strip().upper()
        final_caption = raw_res[1].strip()
        target_channel = CHANNELS.get(category, ADMIN_ID)
    except:
        target_channel = ADMIN_ID
        final_caption = f"Назва: {d['title']}\nПродавець: {user}"

    photo = d.get('photo_id', MYSTERY_BOX_URL)
    
    # ПУБЛІКАЦІЯ
    if d['mode'] == "BUY":
        await bot.send_message(target_channel, final_caption, reply_markup=post_keyboard())
    else:
        await bot.send_photo(target_channel, photo, caption=final_caption, reply_markup=post_keyboard())

    await m.answer("Готово! Твій лот оброблено ШІ та опубліковано. ✅")
    await state.finish()

# --- СЕРВЕР ДЛЯ RENDER ---
async def handle(request): return web.Response(text="Bot is Live")
async def start_webhook():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()

if __name__ == '__main__':
    loop = asyncio.get_event_loop(); loop.create_task(start_webhook())
    executor.start_polling(dp, skip_updates=True)
