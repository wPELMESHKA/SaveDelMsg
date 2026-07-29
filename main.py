import asyncio
import itertools
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message, BusinessConnection, BusinessMessagesDeleted
from config import (
    BOT_API_TOKEN,
    HISTORY_DIR,
    CHANNELS_ARCHIVE_IDS,
    DELETED_MESSAGES_SHOWN,
    SHOW_USER_DELETED_MESSAGES,
)
from db import(
    update_connections_data,
    load_connections
)
os.makedirs(HISTORY_DIR, exist_ok=True)

bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# выполняеться когда кто то включает/выключает или изменяет настройки бота
@dp.business_connection()
async def on_business_connection(connection: BusinessConnection) -> None:
    conn = connection.id
    user = connection.user.id
    update_connections_data(conn, user)


async def main() -> None:
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())