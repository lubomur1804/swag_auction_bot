import os
import asyncio
import logging
import google.generativeai as genai
from aiohttp import web
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

# --- НАЛАШТУВАННЯ ---
API_TOKEN = 'ТВІЙ_ТОКЕН_ТУТ'
GEMINI_KEY = 'ТВІЙ_GEMINI_KEY_ТУТ'

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Швидка модель

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Твої канали (заміни -100... на реальні ID)
CHANNELS = {
    "MERCH": -100,
    "VINTAGE": -100,
    "LUXURY": -100,
    "DENIM": -100,
    "ACCESSORIES": -100,
    "OUTDOOR": -100
}

# --- КНОПКИ ---
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Виставити лот 🔥", callback_data="list"),
        InlineKeyboardButton("Купити 🛍️", url="https://t.me/your_main_channel")
    )
    return keyboard

def restart_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Виставити ще один лот 🔄", callback_data="list"))
    return keyboard

# --- ЛОГІКА БОТА ---
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "Ласкаво просимо на аукціони! 🔥\nВибери дію:",
        reply_markup=main_menu()
    )

@dp.callback_query_handler(lambda c: c.data == 'list')
async def start_listing(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Окей! Надсилай фото та опис лоту одним повідомленням.")

@dp.message_handler(content_types=['photo'])
async def process_lot(message: types.Message):
    if not message.caption:
        await message.reply("Додай опис до фото, щоб я міг зрозуміти, що це за бренд.")
        return

    # Визначаємо категорію через Gemini (приклад твоєї логіки)
    prompt = f"Визнач категорію одягу (MERCH, VINTAGE, LUXURY, DENIM, ACCESSORIES) для: {message.caption}. Відповідай тільки одним словом."
    response = model.generate_content(prompt)
    category = response.text.strip().upper()

    if category in CHANNELS:
        # Пересилаємо в потрібний канал
        await bot.send_photo(CHANNELS[category], message.photo[-1].file_id, caption=message.caption)
        # Фінальне повідомлення БЕЗ смайликів + кнопка "Виставити ще"
        await message.answer(f"Успішно опубліковано на {category}", reply_markup=restart_menu())
    else:
        await message.answer("Не вдалося визначити категорію. Спробуй ще раз.")

# --- ЗАПУСК ---
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_webhook())
    executor.start_polling(dp, skip_updates=True)
