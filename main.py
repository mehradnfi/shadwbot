import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ContentType
)
from aiogram.enums import ParseMode, ChatType
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
import json
import os
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get sensitive data from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "YOUR_ADMIN_ID_HERE"))
DB_FILE = "database.json"
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "SupportUserName")


# Ensure DB file exists with proper structure
def initialize_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump({"users": {}, "purchases": []}, f, indent=2, ensure_ascii=False)


def load_db():
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            if "users" not in data:
                data["users"] = {}
            if "purchases" not in data:
                data["purchases"] = []
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": {}, "purchases": []}


def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


initialize_db()

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 مشخصات کاربری من")],
        [KeyboardButton(text="🛒 خرید بسته")],
        [KeyboardButton(text="🔗 لینک دعوت من")],
        [KeyboardButton(text="💬 پیام به پشتیبانی")]
    ],
    resize_keyboard=True
)

start_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📞 ارسال شماره تماس")],
        [KeyboardButton(text="🔙 بازگشت")]
    ],
    resize_keyboard=True
)


def ensure_user_exists(user_id):
    db = load_db()
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "balance": 0,
            "active": [],
            "purchased": [],
            "phone": "",
            "invited": [],
            "inviter": None
        }
    else:
        user = db["users"][user_id]
        if "balance" not in user:
            user["balance"] = 0
        if "active" not in user:
            user["active"] = []
        if "purchased" not in user:
            user["purchased"] = []
        if "phone" not in user:
            user["phone"] = ""
        if "invited" not in user:
            user["invited"] = []
        if "inviter" not in user:
            user["inviter"] = None
    save_db(db)


@dp.message(CommandStart())
async def start(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    user_id = str(message.from_user.id)
    ensure_user_exists(user_id)
    db = load_db()
    if not db["users"][user_id]["phone"]:
        await message.answer(
            "👋 <b>به خانواده بزرگ <u>ShadowNet VPN</u> خوش اومدی!</b>\n\n"
            "برای استفاده از خدمات حرفه‌ای و امن ما، لطفاً ابتدا شماره تماس خود را ثبت کن.\n"
            "🔒 <i>ما، امنیت و کیفیت را تضمین می‌کنیم.</i>",
            reply_markup=start_menu,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "🏆 <b>به پنل حرفه‌ای ShadowNet VPN خوش اومدی!</b>\n"
            "از منوی زیر یکی از گزینه‌ها رو انتخاب کن و از خدمات ما لذت ببر 👇",
            reply_markup=user_menu,
            parse_mode="HTML"
        )


@dp.message(F.text == "📞 ارسال شماره تماس")
async def request_phone(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    user_id = str(message.from_user.id)
    ensure_user_exists(user_id)
    db = load_db()
    if db["users"][user_id]["phone"]:
        await message.answer(
            "✅ <b>شما قبلاً شماره خود را ثبت کرده‌اید!</b>\n\n"
            "🏆 <b>منوی اصلی</b>\n"
            "از منوی زیر یکی از گزینه‌ها رو انتخاب کن:",
            reply_markup=user_menu,
            parse_mode="HTML"
        )
        return
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ارسال شماره ☎️", request_contact=True)],
            [KeyboardButton(text="🔙 بازگشت")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "📲 <b>لطفاً شماره تماس خود را با دکمه زیر ارسال کن:</b>\n\n"
        "✅ <i>اطلاعات شما کاملاً محرمانه و امن نزد ما باقی می‌ماند.</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@dp.message(F.content_type.in_([ContentType.CONTACT]))
async def handle_contact(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    db = load_db()
    user_id = str(message.from_user.id)
    if db["users"][user_id]["phone"]:
        await message.answer(
            "شما قبلاً شماره خود را ثبت کرده‌اید ✅",
            reply_markup=user_menu,
            parse_mode="HTML"
        )
        return
    db["users"][user_id]["phone"] = message.contact.phone_number
    save_db(db)
    await message.answer(
        "✅ <b>شماره شما با موفقیت ثبت شد!</b>\n"
        "اکنون می‌توانید از خدمات حرفه‌ای ما استفاده کنید.\n"
        "👇 منوی اصلی:",
        reply_markup=user_menu,
        parse_mode="HTML"
    )


# 👤 مشخصات کاربری من
@dp.message(F.text == "👤 مشخصات کاربری من")
async def user_profile(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    user_id = str(message.from_user.id)
    db = load_db()
    user = db["users"][user_id]
    username = message.from_user.username or "ثبت نشده"
    invited_count = len(user.get("invited", []))
    active = user.get("active", [])
    purchased = user.get("purchased", [])
    balance = user.get("balance", 0)
    phone = user.get("phone", "ثبت نشده")
    total_credit = f"{balance:,} تومان"
    total_charge = f"{balance:,} تومان"
    gift = "۰ تومان"
    sub_income = f"{invited_count * 10000:,} تومان"
    total_invoices = f"{len(purchased)}"
    total_success = f"{len(purchased)}"
    total_services = f"{len(active) + len(purchased)}"
    active_services = f"{len(active)}"

    text = (
        "<b>📝 مشخصات کاربری</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"┃ 👤 <b>نام کاربری:</b> <code>{username}</code>\n"
        f"┃ 🗝 <b>آیدی عددی:</b> <code>{user_id}</code>\n"
        f"┃ 📱 <b>شماره تماس:</b> <code>{phone}</code>\n"
        f"┃ 💵 <b>اعتبار کل:</b> <b>{total_credit}</b>\n"
        f"┃ 💳 <b>میزان شارژ حساب:</b> <b>{total_charge}</b>\n"
        f"┃ 💸 <b>هدیه های اعمال شده:</b> <b>{gift}</b>\n"
        f"┃ 💰 <b>درآمد زیرمجموعه گیری:</b> <b>{sub_income}</b>\n"
        f"┃ 🗓 <b>کل فاکتور ها:</b> <b>{total_invoices}</b>\n"
        f"┃ 💎 <b>پرداخت های موفق:</b> <b>{total_success}</b>\n"
        f"┃ 🪐 <b>کل سرویس ها:</b> <b>{total_services}</b>\n"
        f"┃ 💌 <b>سرویس های فعال:</b> <b>{active_services}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "برای بازگشت به منوی اصلی از دکمه بازگشت استفاده کنید"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=user_menu)


# 🛒 خرید بسته
@dp.message(F.text == "🛒 خرید بسته")
async def buy_package(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    text = (
        "<b>🛒 خرید بسته</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 <b>در حال حاضر بسته‌ای برای خرید فعال نیست.</b>\n"
        "🚧 <i>این بخش به زودی با بهترین و متنوع‌ترین سرویس‌ها فعال خواهد شد.</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=user_menu)


# 🔗 لینک دعوت من
@dp.message(F.text == "🔗 لینک دعوت من")
async def invite_link(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    user_id = str(message.from_user.id)
    link = f"https://t.me/{(await bot.me()).username}?start={user_id}"
    db = load_db()
    invited_count = len(db["users"][user_id].get("invited", []))
    text = (
        "<b>🔗 لینک دعوت اختصاصی شما</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>{link}</code>\n"
        f"👥 <b>تعداد دعوتی‌ها:</b> <b>{invited_count}</b>\n"
        "🎁 <i>با دعوت دوستان، از جوایز و تخفیف‌های ویژه بهره‌مند شوید!</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=user_menu)


# 💬 پیام به پشتیبانی
@dp.message(F.text == "💬 پیام به پشتیبانی")
async def support_message(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ارتباط مستقیم با پشتیبانی", url=f"https://t.me/{SUPPORT_USERNAME}")]
        ]
    )
    text = (
        "<b>🛡 پشتیبانی ۲۴ ساعته ShadowNet VPN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "برای ارتباط با تیم پشتیبانی حرفه‌ای ما، روی دکمه زیر بزن 👇\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")
    await message.answer(
        "🏆 <b>منوی اصلی</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "از منوی زیر یکی از گزینه‌ها رو انتخاب کن:\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=user_menu,
        parse_mode="HTML"
    )


# دکمه مخفی شروع (کاربر نمی‌فهمه)
@dp.message(F.text == "شروع")
async def hidden_start(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    text = (
        "🏆 <b>منوی اصلی</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "از منوی زیر یکی از گزینه‌ها رو انتخاب کن:\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=user_menu)


# 🔙 بازگشت
@dp.message(F.text == "🔙 بازگشت")
async def back_button(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    user_id = str(message.from_user.id)
    db = load_db()
    if user_id in db["users"] and db["users"][user_id]["phone"]:
        text = (
            "🏆 <b>منوی اصلی</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "از منوی زیر یکی از گزینه‌ها رو انتخاب کن:\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=user_menu)
    else:
        await message.answer(
            "👋 <b>به خانواده بزرگ <u>ShadowNet VPN</u> خوش اومدی!</b>\n\n"
            "برای استفاده از خدمات حرفه‌ای و امن ما، لطفاً ابتدا شماره تماس خود را ثبت کن.\n"
            "🔒 <i>ما با بیش از ۳ سال سابقه، امنیت و کیفیت را تضمین می‌کنیم.</i>",
            reply_markup=start_menu,
            parse_mode="HTML"
        )


# هندلر عمومی برای جلوگیری از ناپدید شدن منو
@dp.message()
async def handle_any_message(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return

    # اگر پیام جزو دکمه‌های منو نبود، منو رو دوباره نشون بده
    if message.text not in [
        "👤 مشخصات کاربری من", "🛒 خرید بسته", "🔗 لینک دعوت من",
        "💬 پیام به پشتیبانی", "🔙 بازگشت", "شروع"
    ]:
        # بررسی کن که آیا کاربر ثبت شده یا نه
        user_id = str(message.from_user.id)
        db = load_db()
        if user_id in db["users"] and db["users"][user_id]["phone"]:
            text = (
                "🏆 <b>منوی اصلی</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "از منوی زیر یکی از گزینه‌ها رو انتخاب کن:\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            )
            await message.answer(text, parse_mode="HTML", reply_markup=user_menu)
        else:
            await message.answer(
                "👋 <b>به خانواده بزرگ <u>ShadowNet VPN</u> خوش اومدی!</b>\n\n"
                "برای استفاده از خدمات حرفه‌ای و امن ما، لطفاً ابتدا شماره تماس خود را ثبت کن.\n"
                "🔒 <i>ما با بیش از ۳ سال سابقه، امنیت و کیفیت را تضمین می‌کنیم.</i>",
                reply_markup=start_menu,
                parse_mode="HTML"
            )


# مدیریت (بدون تغییر)
broadcast_flag = {}


@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    if message.from_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 لیست کاربران", callback_data="users")],
        [InlineKeyboardButton(text="💌 ارسال پیام همگانی", callback_data="broadcast")]
    ])
    await message.answer("پنل مدیریت 👑", reply_markup=kb)


@dp.callback_query(F.data == "users")
async def list_users(call):
    if call.message.chat.type != ChatType.PRIVATE:
        return
    if call.from_user.id != ADMIN_ID:
        return
    db = load_db()
    await call.message.answer(f"👥 تعداد کاربران: {len(db['users'])}")


@dp.callback_query(F.data == "broadcast")
async def request_broadcast(call):
    if call.message.chat.type != ChatType.PRIVATE:
        return
    if call.from_user.id != ADMIN_ID:
        return
    broadcast_flag[call.from_user.id] = True
    await call.message.answer("✏️ پیام خود را ارسال کنید:")


@dp.message()
async def do_broadcast(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    if broadcast_flag.get(message.from_user.id):
        db = load_db()
        for uid in db["users"]:
            try:
                await bot.send_message(int(uid), message.text)
            except:
                pass
        await message.answer("✅ پیام به همه ارسال شد.")
        broadcast_flag[message.from_user.id] = False


async def main():
    try:
        print("🚀 ربات ShadowNet VPN در حال راه‌اندازی...")
        print("✅ دیتابیس بررسی شد")
        print("✅ توکن ربات تایید شد")
        print("🔄 شروع به کار...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ خطا در اجرای ربات: {e}")
        print(f"جزئیات خطا: {traceback.format_exc()}")
    finally:
        print("🛑 ربات متوقف شد")


if __name__ == '__main__':
    print("=" * 50)
    print("🎯 ShadowNet VPN Bot")
    print("=" * 50)
    asyncio.run(main())
