import asyncio
import logging
import aiogram

from aiogram import Dispatcher, F, types
from app.handlers import router
from app.handlers import bot as bt

from app.database.models import async_main


async def main():
    await async_main()
    bot = bt
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot, allowed_updates=["message", "chat_member", "my_chat_member", "channel_post", "callback_query"])

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')