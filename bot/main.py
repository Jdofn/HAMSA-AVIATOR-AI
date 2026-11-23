import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from app.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "مرحباً بك في HAMSA AVIATOR AI Research.\n"
        "الإصدار الحالي: Phase 01 Foundation.\n"
        "مصدر النتائج الرسمي لم يتم ربطه بعد."
    )

@dp.message(Command("status"))
async def status(message: Message):
    await message.answer(
        "HAMSA AVIATOR AI\n"
        "API: منفصل عن البوت\n"
        "Data source: غير مهيأ\n"
        "Research mode: مفعّل"
    )

async def main():
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Configure it in Railway Variables.")
    bot = Bot(token=settings.telegram_bot_token)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
