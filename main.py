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
    DELETED_MESSAGES_SHOWN
)
from db_conns import(
    update_connections_data,
    load_connections
)
from db_msgs import(
    save_msg
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
    await update_connections_data(conn, user)


@dp.business_message()
async def on_business_message(message: Message) -> None:
    await save_msg(message, bot)


async def main() -> None:
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())