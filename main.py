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
GEMINI_KEY = 'ВСТАВ_СВІЙ_КЛЮЧ' # Сюди встав ключ від Google AI
ADMIN_ID = 5055318931
MYSTERY_BOX_URL = "https://i.ibb.co/6R0yX0P/mystery-box.jpg" # Твоє фото боксу

# Канали (всі ID твої)
CHANNELS = {
    "VINTAGE": -1002283307774,
    "LUXURY": -1002283307774,
    "DENIM": -1002283307774,
    "OUTDOOR": -1002283307774,
    "MERCH": -1002283307774,
    "ACCESSORIES": -1002283307774
}

# Ініціалізація
logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class OrderState(StatesGroup):
    mode = State()
    title = State(); size = State(); condition = State()
    price = State(); step = State(); buyout = State()
    delivery = State(); payment = State(); photo = State()

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

# --- ХЕНДЛЕРИ ---
@dp.message_handler(commands=['start'], state="*")
async def cmd_start(m: types.Message, state: FSMContext):
    await state.finish()
    await m.answer("Вибери дію, бро:", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data.startswith('set_'), state="*")
async def start_flow(c: types.CallbackQuery, state: FSMContext):
    mode = c.data.split('_')[1]
    await state.update_data(mode=mode)
    await OrderState.title.set()
    labels = {"LOT": "Назва речі:", "BUY": "Що купити?", "BOX": "Назва боксу:", "PACK": "Назва паку:"}
    await bot.send_message(c.from_user.id, labels[mode])

@dp.message_handler(state=OrderState.title)
async def st_1(m: types.Message, state: FSMContext):
    await state.update_data(title=m.text); await OrderState.size.set(); await m.answer("Розмір:")

@dp.message_handler(state=OrderState.size)
async def st_2(m: types.Message, state: FSMContext):
    await state.update_data(size=m.text); await OrderState.condition.set(); await m.answer("Стан:")

@dp.message_handler(state=OrderState.condition)
async def st_3(m: types.Message, state: FSMContext):
    await state.update_data(condition=m.text); await OrderState.price.set()
    d = await state.get_data()
    await m.answer("Бюджет:" if d['mode'] == "BUY" else "Старт:")

@dp.message_handler(state=OrderState.price)
async def st_4(m: types.Message, state: FSMContext):
    await state.update_data(price=m.text)
    d = await state.get_data()
    if d['mode'] == "BUY": await OrderState.delivery.set(); await m.answer("Відправлення:")
    else: await OrderState.step.set(); await m.answer("Крок:")

@dp.message_handler(state=OrderState.step)
async def st_5(m: types.Message, state: FSMContext):
    await state.update_data(step=m.text); await OrderState.buyout.set(); await m.answer("Викуп:")

@dp.message_handler(state=OrderState.buyout)
async def st_6(m: types.Message, state: FSMContext):
    await state.update_data(buyout=m.text); await OrderState.delivery.set(); await m.answer("Відправляю:")

@dp.message_handler(state=OrderState.delivery)
async def st_7(m: types.Message, state: FSMContext):
    await state.update_data(delivery=m.text); await OrderState.payment.set(); await m.answer("Оплата:")

@dp.message_handler(state=OrderState.payment)
async def st_8(m: types.Message, state: FSMContext):
    await state.update_data(payment=m.text)
    d = await state.get_data()
    if d['mode'] in ["BOX", "BUY"]: await finish_order(m, state)
    else: await OrderState.photo.set(); await m.answer("📸 Надішліть фото:")

@dp.message_handler(content_types=['photo'], state=OrderState.photo)
async def st_photo(m: types.Message, state: FSMContext):
    await state.update_data(photo_id=m.photo[-1].file_id)
    await finish_order(m, state)

async def finish_order(m: types.Message, state: FSMContext):
    d = await state.get_data()
    user = f"@{m.from_user.username}" if m.from_user.username else "@swagking61"

    # --- СИСТЕМА ШІ ТА РОЗПОДІЛУ (ЛОТ І ПАК ПРАЦЮЮТЬ ОДНАКОВО) ---
    prompt = f"""
    Ти адмін аукціону. Тобі надіслали дані для: {d['mode']}.
    Дані: Назва: {d['title']}, Розмір: {d['size']}, Стан: {d['condition']}, Старт/Бюджет: {d.get('price','')}, Крок: {d.get('step','')}, Викуп: {d.get('buyout','')}, Доставка: {d.get('delivery','')}, Оплата: {d['payment']}.

    1. Визнач категорію ОДНИМ словом: LUXURY, VINTAGE, DENIM, OUTDOOR, MERCH або ACCESSORIES.
    2. Якщо це ПАК (PACK), зроби заголовок '🧺 ПАК РЕЧЕЙ'.
    3. Сформуй текст СУВОРО за шаблоном:
    
    Назва: {d['title']}
    Розмір: {d['size']}
    Стан: {d['condition']}
    
    Старт: {d.get('price','')}
    Крок: {d.get('step','')}
    Викуп: {d.get('buyout','')}
    
    Відправляю: {d.get('delivery','')}
    Оплата: {d['payment']}
    
    Продавець - {user}
    Кінець через 24 години після останньої ставки.
    
    Відповідь дай у форматі: КАТЕГОРІЯ ||| ТЕКСТ_ПОСТА
    """
    
    try:
        res = ai_model.generate_content(prompt).text.split("|||")
        cat, caption = res[0].strip().upper(), res[1].strip()
        target = CHANNELS.get(cat, ADMIN_ID)
    except:
        target, caption = ADMIN_ID, f"Назва: {d['title']}\nПродавець: {user}"

    photo = d.get('photo_id', MYSTERY_BOX_URL)
    
    if d['mode'] == "BUY":
        await bot.send_message(target, caption, reply_markup=post_keyboard())
    else:
        await bot.send_photo(target, photo, caption=caption, reply_markup=post_keyboard())

    await m.answer(f"Готово! Виставлено в {cat}. ✅"); await state.finish()

# --- СЕРВЕР ---
async def handle(request): return web.Response(text="Bot is running!")
async def start_webhook():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()

if __name__ == '__main__':
    loop = asyncio.get_event_loop(); loop.create_task(start_webhook())
    executor.start_polling(dp, skip_updates=True)
