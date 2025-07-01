import asyncio
import json
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram.enums import ParseMode, ChatType
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from fastapi import FastAPI
from threading import Thread
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "SupportUserName")
DB_FILE = "database.json"

# DB Helpers
def initialize_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump({"users": {}, "purchases": []}, f, indent=2, ensure_ascii=False)

def load_db():
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"users": {}, "purchases": []}

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

initialize_db()

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="👤 مشخصات کاربری من")],
    [KeyboardButton(text="🛒 خرید بسته")],
    [KeyboardButton(text="🔗 لینک دعوت من")],
    [KeyboardButton(text="💬 پیام به پشتیبانی")]
], resize_keyboard=True)

start_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📞 ارسال شماره تماس", request_contact=True)],
], resize_keyboard=True)

def ensure_user(user_id):
    db = load_db()
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "balance": 0, "active": [], "purchased": [],
            "phone": "", "invited": [], "inviter": None
        }
        save_db(db)

@dp.message(CommandStart())
async def start(message: Message):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    db = load_db()
    if not db["users"][user_id]["phone"]:
        await message.answer(
            "👋 <b>به ShadowNet VPN خوش اومدی</b>
"
            "لطفاً شماره‌ت رو ثبت کن:", reply_markup=start_menu)
    else:
        await message.answer("🏁 منوی اصلی:", reply_markup=user_menu)

@dp.message(F.contact)
async def contact_handler(message: Message):
    user_id = str(message.from_user.id)
    db = load_db()
    db["users"][user_id]["phone"] = message.contact.phone_number
    save_db(db)
    await message.answer("✅ شماره ثبت شد!", reply_markup=user_menu)

@dp.message(F.text == "👤 مشخصات کاربری من")
async def profile(message: Message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db["users"][user_id]
    txt = (
        f"<b>🧾 پروفایل کاربر</b>
"
        f"👤 یوزرنیم: @{message.from_user.username or 'ثبت نشده'}
"
        f"🆔 آیدی: <code>{user_id}</code>
"
        f"📱 تلفن: <code>{user['phone'] or 'ثبت نشده'}</code>
"
        f"💰 اعتبار: {user['balance']} تومان
"
        f"👥 دعوتی‌ها: {len(user['invited'])}"
    )
    await message.answer(txt, reply_markup=user_menu)

@dp.message(F.text == "🔗 لینک دعوت من")
async def invite(message: Message):
    user_id = str(message.from_user.id)
    bot_user = await bot.me()
    link = f"https://t.me/{bot_user.username}?start={user_id}"
    db = load_db()
    invited_count = len(db["users"][user_id]["invited"])
    await message.answer(
        f"<b>🔗 لینک دعوت شما:</b>
<code>{link}</code>
"
        f"👥 تعداد دعوت‌شده‌ها: {invited_count}", reply_markup=user_menu)

@dp.message(F.text == "🛒 خرید بسته")
async def buy(message: Message):
    await message.answer("🛍 خرید سرویس به‌زودی فعال می‌شود.", reply_markup=user_menu)

@dp.message(F.text == "💬 پیام به پشتیبانی")
async def support(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ارتباط با پشتیبانی", url=f"https://t.me/{SUPPORT_USERNAME}")]
    ])
    await message.answer("🛡 برای تماس با پشتیبانی، دکمه زیر را بزنید:", reply_markup=kb)

# Web Server
app = FastAPI()
@app.get("/")
async def root():
    return {"status": "bot is alive"}

def run_web():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    Thread(target=run_web).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
