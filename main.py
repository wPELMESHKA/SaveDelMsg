import asyncio
import logging
from html import escape
import os
from blacklist import is_blacklisted
from aiogram import Bot, Dispatcher
from aiogram.types import Message, BusinessConnection, BusinessMessagesDeleted
from config import(
    BOT_API_TOKEN,
    DATA_FOLDER,
    DELETED_MESSAGES_SHOWN,
    BLACKLIST_FILE_NAME
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

os.makedirs(DATA_FOLDER, exist_ok=True)
with open(os.path.join(DATA_FOLDER, BLACKLIST_FILE_NAME), "a", encoding="utf-8") as f:
    pass

bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# выполняеться когда кто то включает/выключает или изменяет настройки бота
@dp.business_connection()
async def on_business_connection(connection: BusinessConnection) -> None:
    if is_blacklisted(connection.user.id):
        return
    
    conn = connection.id
    user = connection.user.id
    await update_connections_data(conn, user)


@dp.business_message()
async def on_business_message(message: Message) -> None:
    if _userID_by_connID(message.business_connection_id) is None:
        await restore_connection(message.business_connection_id, bot)

    if message.text and message.text.startswith("."):
        if await dot_commands(message, bot):
            return

    await save_msg(message, bot)


@dp.deleted_business_messages()
async def on_deleted_business_message(event: BusinessMessagesDeleted):
    # айди владельца акаунта
    userID = _userID_by_connID(event.business_connection_id)
    if not userID:
        return

    if is_blacklisted(userID):
        return
    
    # айди диалога
    chatID = event.chat.id

    data = load_data(userID, chatID)
    if not data:
        return

    msgs_to_show = []
    for msg_id in event.message_ids:
        if not data.get(str(msg_id)):
            continue
        else: 
            msgs_to_show.append(msg_id)
    
    for msg_id in msgs_to_show[:DELETED_MESSAGES_SHOWN]:
        await bot.send_message(
            chat_id=int(userID),
            text=(
                f"<b>Сообщение удалено в чате с:</b>\n"
                f"<code>{escape(data[str(msg_id)]['partner_name'])}</code> <b>(</b><code>{chatID}</code><b>)</b>\n"
                f"<b>Сообщение было отправлено в:</b>\n"
                f"{escape(data[str(msg_id)]['time'])} (UTC+0)"
                ),
            parse_mode="HTML"
        )

        if data[str(msg_id)]["channel_id"]:
            try:
                await bot.copy_message(
                chat_id=int(userID),
                from_chat_id=data[str(msg_id)]["channel_id"],
                message_id=data[str(msg_id)]["channel_msg_id"],
            )

            except Exception:
                logging.exception("Не удалось скопировать сообщение из архива")
                await bot.send_message(chat_id=int(userID),  text="Не удалось скопировать сообщение из архива")

        else:
            await bot.send_message(
                chat_id=int(userID), 
                text=data[str(msg_id)]["text"],
                parse_mode="HTML"
                )

    if len(msgs_to_show) > DELETED_MESSAGES_SHOWN:
         await bot.send_message(
            chat_id=int(userID), 
            text=f"<b>Удалено еще {len(msgs_to_show) - DELETED_MESSAGES_SHOWN} сообщений</b>",
            parse_mode="HTML"
            )


async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())