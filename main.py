import asyncio
import logging
from html import escape
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message, BusinessConnection, BusinessMessagesDeleted
from config import (
    BOT_API_TOKEN,
    HISTORY_DIR,
    DELETED_MESSAGES_SHOWN
)
from db_conns import(
    update_connections_data,
    restore_connection
)
from db_msgs import(
    save_msg,
    _userID_by_connID,
    load_data
)
from dot_commands import(
    dot_commands
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
    if _userID_by_connID(message.business_connection_id) is None:
        await restore_connection(message.business_connection_id, bot)

    if message.text and message.text.startswith("."):
        await dot_commands(message, bot)
        
    await save_msg(message, bot)


@dp.deleted_business_messages()
async def on_deleted_business_message(event: BusinessMessagesDeleted):
    # айди владельца акаунта
    userID = _userID_by_connID(event.business_connection_id)
    if not userID:
        return
    # айди диалога
    chatID = event.chat.id

    data = load_data(userID, chatID)
    if not data:
        return

    msg_showed = 0
    for i in range(min(DELETED_MESSAGES_SHOWN, len(event.message_ids))):
        # айди сообщения
        msgID = event.message_ids[i]
        
        if not data.get(str(msgID)):
            continue

        await bot.send_message(
            chat_id=int(userID), 
            text=(
                f"<b>Сообщение удалено в чате с:</b>\n"
                f"<code>{escape(data[str(msgID)]['partner_name'])}</code> <b>(</b><code>{chatID}</code><b>)</b>\n"
                f"<b>Сообщение было отправлено в:</b>\n"
                f"{escape(data[str(msgID)]['time'])} (UTC+0)"
                ),
            parse_mode="HTML"
        )
        msg_showed += 1

        if data[str(msgID)]["channel_id"]:
            try:
                await bot.copy_message(
                chat_id=int(userID),
                from_chat_id=data[str(msgID)]["channel_id"],
                message_id=data[str(msgID)]["channel_msg_id"],
            )

            except Exception:
                logging.exception("Не удалось скопировать сообщение из архива")

        else:
            await bot.send_message(
                chat_id=int(userID), 
                text=data[str(msgID)]["text"],
                parse_mode="HTML"
                )

    all_del_msg = 0
    for i in event.message_ids:
        if str(i) in data:
            all_del_msg += 1
    if all_del_msg > msg_showed:
         await bot.send_message(
            chat_id=int(userID), 
            text=f"<b>Удалено еще {all_del_msg - msg_showed} сообщений</b>",
            parse_mode="HTML"
            )


async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())