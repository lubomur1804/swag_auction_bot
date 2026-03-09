import logging
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

# === КОНФІГУРАЦІЯ ===
API_TOKEN = '8294128537:AAE8G3c23bhBqsqHTKjBcd7Oq-e6NhdjrVM' 
GEMINI_KEY = 'AIzaSyC6Cv7zsfFcb5WNEIgMppGi_28iR6LM054'

CHANNELS = {
    "MERCH": "@swagmerchauction",
    "LUXURY": "@swagluxuryauction",
    "VINTAGE": "@swagvintageauction",
    "DENIM": "@swagdenimauction",
    "ACCESSORIES": "@swagaccessories",
    "OUTDOOR": "@swagoutdoor",
    "JERSEY": "@extazy_auction",
    "SNEAKERS": "@swagsneakersauction"
}

CH_NAMES = {
    "MERCH": "MERCH 👕", "LUXURY": "LUXURY 💍", "VINTAGE": "VINTAGE 🏛️",
    "DENIM": "DENIM 👖", "ACCESSORIES": "ACCESSORIES 👜", "OUTDOOR": "OUTDOOR 🏔️",
    "JERSEY": "JERSEY ⚽", "SNEAKERS": "SNEAKERS AUCTION 👟" # Змінено тут
}

URL_RULES = "https://t.me/swagplabyla"
URL_GARANT = "https://t.me/swagking61"
URL_BOT = "https://t.me/swag_manager_bot"

genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class Form(StatesGroup):
    mode = State()
    rules_agree = State()
    title = State()
    size = State()
    condition = State()
    money = State()
    step = State()
    buyout = State()
    delivery = State()
    payment = State()
    photos = State()

# === ЛОГІКА ===

@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("Виставити лот 🏷️", "Купити 💸")
    await Form.mode.set()
    await message.answer("Ласкаво просимо на наші аукціони! 🛍️", reply_markup=kb)

@dp.message_handler(state=Form.mode)
async def set_mode(message: types.Message, state: FSMContext):
    mode = "SELL" if "Виставити" in message.text else "BUY"
    await state.update_data(mode=mode)
    await Form.rules_agree.set()
    ikb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Ознайомився ✅", callback_data="rules_ok"))
    msg_rules = f"Спочатку прошу ознайомитися з <a href='{URL_RULES}'>ПРАВИЛАМИ</a>, у разі порушення передбачено <b>БАН</b>, заповніть шаблон та скиньте сюди"
    await message.answer(msg_rules, reply_markup=ikb, parse_mode="HTML", disable_web_page_preview=True)

@dp.callback_query_handler(text="rules_ok", state=Form.rules_agree)
async def rules_accepted(call: types.CallbackQuery, state: FSMContext):
    await Form.title.set()
    data = await state.get_data()
    text = "Назва лоту (Бренд + Річ):" if data['mode'] == "SELL" else "Що саме шукаєте?:"
    await bot.send_message(call.from_user.id, text, reply_markup=types.ReplyKeyboardRemove())
    await call.answer()

@dp.message_handler(state=Form.title)
async def p_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await Form.size.set()
    await message.answer("Розмір:")

@dp.message_handler(state=Form.size)
async def p_size(message: types.Message, state: FSMContext):
    await state.update_data(size=message.text)
    await Form.condition.set()
    await message.answer("Стан (0/10):")

@dp.message_handler(state=Form.condition)
async def p_cond(message: types.Message, state: FSMContext):
    await state.update_data(condition=message.text)
    data = await state.get_data()
    await Form.money.set()
    await message.answer("Старт (грн):" if data['mode'] == "SELL" else "Бюджет (грн):")

@dp.message_handler(state=Form.money)
async def p_money(message: types.Message, state: FSMContext):
    await state.update_data(money=message.text)
    data = await state.get_data()
    if data['mode'] == "SELL":
        await Form.step.set()
        await message.answer("Крок:")
    else:
        await Form.delivery.set()
        await message.answer("Відправляю:") # Змінено тут

@dp.message_handler(state=Form.step)
async def p_step(message: types.Message, state: FSMContext):
    await state.update_data(step=message.text)
    await Form.buyout.set()
    await message.answer("Викуп:")

@dp.message_handler(state=Form.buyout)
async def p_buyout(message: types.Message, state: FSMContext):
    await state.update_data(buyout=message.text)
    await Form.delivery.set()
    await message.answer("Відправляю:") # Змінено тут

@dp.message_handler(state=Form.delivery)
async def p_deliv(message: types.Message, state: FSMContext):
    await state.update_data(delivery=message.text)
    await Form.payment.set()
    await message.answer("Спосіб оплати:")

@dp.message_handler(state=Form.payment)
async def p_pay(message: types.Message, state: FSMContext):
    await state.update_data(payment=message.text, photos=[])
    await Form.photos.set()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("ГОТОВО ✅")
    await message.answer("📸 Надішліть до 8 фото, потім натисніть ГОТОВО", reply_markup=kb)

@dp.message_handler(content_types=['photo'], state=Form.photos)
async def p_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data['photos']
    if len(photos) < 8:
        if len(photos) == 0: await message.photo[-1].download('check.jpg')
        photos.append(message.photo[-1].file_id)
        await state.update_data(photos=photos)

@dp.message_handler(state=Form.photos, text="ГОТОВО ✅")
async def process_all(message: types.Message, state: FSMContext):
    await message.answer("🤖 Секунду, вибираю найкращий канал для твого лоту...")
    data = await state.get_data()
    t = data['title'].lower()
    
    DB = {
        "LUXURY": ["stone", "island", "стон", "айленд", "си", "si", "cp company", "ср", "цп", "moncler", "gucci", "prada", "dior", "lv", "vuitton", "armani", "rolex", "diesel", "balenciaga", "burberry", "versace", "fendi", "trapstar", "corteiz", "stoney", "патч"],
        "OUTDOOR": ["arc", "teryx", "arcteryx", "арк", "арктерікс", "tnf", "north face", "patagonia", "mammut", "salomon", "haglofs", "marmot", "berghaus", "oakley", "gore", "tex", "vibram", "wolfskin"],
        "SNEAKERS": ["nike", "adidas", "jordan", "nb", "balance", "asics", "vans", "puma", "кросівки", "кеди", "взуття", "yeezy", "dunk", "force", "max", "tn", "gazelle", "samba", "найк", "адідас"],
        "DENIM": ["levis", "levi's", "evisu", "polar", "big boy", "джинси", "denim", "wrangler", "lee", "carhartt single", "double knee", "левайс"],
        "JERSEY": ["jersey", "джерсі", "футболка", "майка", "форма", "футбольна", "t-shirt", "football", "баскетбольна"],
        "ACCESSORIES": ["watch", "годинник", "bag", "сумка", "рюкзак", "кепка", "cap", "ремень", "окуляри", "wallet", "гаманець", "beanie", "бананка", "шапка"],
        "VINTAGE": ["vintage", "вінтаж", "90s", "80s", "retro", "ретро", "олімпійка"]
    }

    final_cat = "MERCH"
    found = False

    for cat_name, keys in DB.items():
        if any(key in t for key in keys):
            final_cat = cat_name
            found = True
            break
    
    if not found:
        try:
            img = genai.upload_file("check.jpg")
            prompt = f"Ти сортувальник одягу. Назва: '{data['title']}'. Категорія з: MERCH, LUXURY, VINTAGE, DENIM, ACCESSORIES, OUTDOOR, JERSEY, SNEAKERS. Тільки 1 слово."
            response = ai_model.generate_content([prompt, img])
            ai_choice = response.text.strip().upper()
            if ai_choice in CHANNELS: final_cat = ai_choice
        except: final_cat = "MERCH"

    target = CHANNELS[final_cat]
    user = f"@{message.from_user.username}" if message.from_user.username else "Користувач"
    footer = f"\n\n<a href='{URL_BOT}'>ВИСТАВИТИ ЛОТ</a> | <a href='{URL_RULES}'>ПРАВИЛА</a> | <a href='{URL_GARANT}'>ГАРАНТ</a>"
    
    if data['mode'] == "SELL":
        caption = (f"Назва: {data['title']}\n\n"
                   f"Розмір: {data['size']}\n"
                   f"Стан: {data['condition']}\n\n"
                   f"Старт: {data['money']}\n"
                   f"Крок: {data.get('step', '50')}\n"
                   f"Викуп: {data.get('buyout', '-')}\n\n"
                   f"Відправляю: {data['delivery']}\n"
                   f"Оплата: {data['payment']}\n\n"
                   f"Продавець - {user}\n"
                   f"Кінець через 24 години після останньої ставки."
                   f"{footer}")
    else:
        caption = (f"Шукаю: {data['title']}\n\n"
                   f"Розмір: {data['size']}\n"
                   f"Бюджет: {data['money']}\n\n"
                   f"Покупець - {user}"
                   f"{footer}")

    media = types.MediaGroup()
    for i, p in enumerate(data['photos']):
        media.attach_photo(p, caption=caption if i == 0 else "", parse_mode="HTML")
    
    try:
        await bot.send_media_group(target, media)
        # Змінено тут: "Опубліковано" замість "Автоматично опубліковано"
        await message.answer(f"🚀 Опубліковано в канал <b>{CH_NAMES[final_cat]}</b>!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Помилка: {e}")
    
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)