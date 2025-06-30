import asyncio
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.handlers import start_handler

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_handler.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
