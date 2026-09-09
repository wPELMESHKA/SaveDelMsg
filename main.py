import asyncio
import logging
from html import escape
import os


from aiogram import Bot, Dispatcher
from aiogram.types import Message, BusinessConnection, BusinessMessagesDeleted

from config import (
    BOT_API_TOKEN,
    DATA_FOLDER,
    DELETED_MESSAGES_SHOWN
)
from db_conns import (
    get_user_id_by_conn_id,
    init_connections_table,
    remove_connection,
    add_connection,
    restore_connection
)
from db_msgs import (
    data_preparation,
    get_msg,
    init_messages_table
)
from dot_commands import (
    dot_commands
)
from blacklist import (
    is_blacklisted
)


os.makedirs(DATA_FOLDER, exist_ok=True)
with open(os.path.join(DATA_FOLDER, "blacklist.txt"), "a", encoding="utf-8") as f:
    pass



bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# выполняеться когда кто то включает/выключает или изменяет настройки бота
@dp.business_connection()
async def on_business_connection(connection: BusinessConnection) -> None:
    if is_blacklisted(connection.user.id) and connection.is_enabled:
        await remove_connection(connection.id)
        return

    # Проверяем добавлено ли подключение или удалено
    if connection.is_enabled:
        await add_connection(connection.id, connection.user.id)
    else:
        await remove_connection(connection.id)


@dp.business_message()
async def on_business_message(message: Message) -> None:
    if await get_user_id_by_conn_id(message.business_connection_id) is None:
        await restore_connection(message.business_connection_id, bot)

    if message.text and message.text.startswith("."):
        await dot_commands(message, bot)

    await data_preparation(message, bot)


@dp.deleted_business_messages()
async def on_deleted_business_message(event: BusinessMessagesDeleted):
    # айди владельца акаунта
    user_id = await get_user_id_by_conn_id(event.business_connection_id)
    if not user_id:
        return

    if is_blacklisted(user_id):
        return
    
    # айди диалога
    chat_id = event.chat.id

    msgs_to_show = []
    for msg_id in event.message_ids:
        msg = await get_msg(str(user_id), str(chat_id), str(msg_id))
        if msg and not msg[3].endswith("(Владелец аккаунта)"):
            msgs_to_show.append(msg)

    for msg in msgs_to_show[:DELETED_MESSAGES_SHOWN]:
        sender_name = msg[3].replace(" (Собеседник)", "")
        channel_id = msg[4]
        channel_msg_id = msg[5]
        msg_text = msg[6]
        msg_time = msg[7]

        await bot.send_message(
            chat_id=int(user_id),
            text=(
                f"<b>Сообщение удалено в чате с:</b>\n"
                f"<code>{escape(sender_name)}</code> <b>(</b><code>{chat_id}</code><b>)</b>\n"
                f"<b>Сообщение было отправлено в:</b>\n"
                f"{escape(msg_time)} (UTC+0)"
                ),
            parse_mode="HTML"
        )

        await asyncio.sleep(1)  # чтобы не спамить слишком быстро и не получить ошибку от Telegram API

        if channel_id and channel_msg_id:
            try:
                await bot.copy_message(
                chat_id=int(user_id),
                from_chat_id=int(channel_id),
                message_id=int(channel_msg_id),
            )

            except Exception:
                logging.exception("Не удалось скопировать сообщение из архива")
                await bot.send_message(chat_id=int(user_id),  text="Не удалось скопировать сообщение из архива")

        else:
            await bot.send_message(
                chat_id=int(user_id),
                text=msg_text,
                parse_mode="HTML"
                )
            
        await asyncio.sleep(1)  # чтобы не спамить слишком быстро и не получить ошибку от Telegram API

    if len(msgs_to_show) > DELETED_MESSAGES_SHOWN:
         await bot.send_message(
            chat_id=int(user_id), 
            text=f"<b>Удалено еще {len(msgs_to_show) - DELETED_MESSAGES_SHOWN} сообщений</b>",
            parse_mode="HTML"
            )


async def main():
    print("Бот запущен")
    await init_connections_table()
    await init_messages_table()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())