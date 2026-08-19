from html import escape
import asyncio
import logging
import os
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import Message
import aiosqlite

from config import (
    DATA_FOLDER,
    CHANNELS_ARCHIVE_IDS
)
from db_conns import (
    get_user_id_by_conn_id
)


MESSAGES_FILE_PATH = os.path.join(DATA_FOLDER, "messages.db")

channel_index = 0
channel_lock = asyncio.Lock()
async def get_next_channel() -> str:
    # берет текущий канал и переключает на следуюший с локом
    global channel_index
    async with channel_lock:
        chosen_channel = CHANNELS_ARCHIVE_IDS[channel_index]
        channel_index = (channel_index + 1) % len(CHANNELS_ARCHIVE_IDS)
        return chosen_channel



# инициализирует таблицу если она не существует
async def init_messages_table():
    async with aiosqlite.connect(MESSAGES_FILE_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                user_id TEXT,
                chat_id TEXT,
                msg_id TEXT,
                name TEXT,
                channel_id TEXT,
                channel_msg_id TEXT,
                text TEXT,
                time TEXT,
                PRIMARY KEY (user_id, chat_id, msg_id)
            )
        """)

        await db.commit()



# проверка на все типы сообщений
async def data_preparation(message: Message, bot: Bot):
    # получаем айди владельца акаунта
    user_id = await get_user_id_by_conn_id(message.business_connection_id)
    if user_id is None:
        return

    # когда в личку пишут от имени канала то message.from_user.id вообще не будет и код упадет 
    if message.from_user:
        if user_id == str(message.from_user.id):
            name = f"{message.from_user.full_name} (Владелец аккаунта)"
            return 
        else: 
            name = f"{message.from_user.full_name} (Собеседник)"
    else:
        name = "Неизвестный пользователь (от имени канала)"

    # ID собеседника
    chat_id = str(message.chat.id)
    # ID сообщения
    msg_id = str(message.message_id)
    # Подпись к фото или видео (будет str или None)
    caption = message.caption
    
    time = datetime.now(timezone.utc).strftime("%H:%M %d.%m.%Y")

    # 1. Обычный текст
    if message.text:
        text = escape(message.text)
        await save_msg((user_id, chat_id, msg_id, name, None, None, text, time))


    # 2. Интерактивный  эмодзи (🎲/🎯/🏀/⚽/🎳/🎰)
    elif message.dice:
        text = f"Интерактивный эмодзи: {message.dice.emoji} (Значение: {message.dice.value})"
        await save_msg((user_id, chat_id, msg_id, name, None, None, text, time))

        
    # 3. Геолокация
    elif message.location:
        text = (
            f"Геолокация:\n"
            f"Координата Х (Долгота): {message.location.longitude}\n"
            f"Координата Y (Широта): {message.location.latitude}\n"
            f'<a href="https://maps.google.com/?q={message.location.latitude},{message.location.longitude}">Открыть на Google картах</a>'
        )
        await save_msg((user_id, chat_id, msg_id, name, None, None, text, time))


    # 4. Контакт (Номер телефона)
    elif message.contact:
        text = (
            f"Имя контакта: {escape(message.contact.full_name)}\n"
            f"Номер телефона контакта: {escape(message.contact.phone_number)}"
        )
        await save_msg((user_id, chat_id, msg_id, name, None, None, text, time))

    # 5. Место (Venue)
    elif message.venue:
        text = (
            f"Место: {escape(message.venue.title)}\n"
            f"Адрес: {escape(message.venue.address)}\n"
            f'<a href="https://maps.google.com/?q={message.venue.location.latitude},{message.venue.location.longitude}">Открыть на Google картах</a>'
        )
        await save_msg((user_id, chat_id, msg_id, name, None, None, text, time))


    # все медиа которые надо отправлять в канал
    else:    
        try:
            # 6. Фотография
            if message.photo:
                # Отправляем в канал по file_id
                saved_in_channel = await bot.send_photo(
                    chat_id=await get_next_channel(),
                    photo=message.photo[-1].file_id, # Самое лучшее качество,
                    caption=caption
                )
            # 7. Видео
            elif message.video:
                saved_in_channel = await bot.send_video(
                    chat_id=await get_next_channel(),
                    video=message.video.file_id,
                    caption=caption
                )
            # 8. Голосовое сообщение (Voice)
            elif message.voice:
                saved_in_channel = await bot.send_voice(
                    chat_id=await get_next_channel(),
                    voice=message.voice.file_id
                )
            # 9. Видеосообщение (Кружочек / Video Note)
            elif message.video_note:
                saved_in_channel = await bot.send_video_note(
                    chat_id=await get_next_channel(),
                    video_note=message.video_note.file_id
                )
            # 10. ГИФ-анимация (Animation)
            elif message.animation:
                saved_in_channel = await bot.send_animation(
                    chat_id=await get_next_channel(),
                    animation=message.animation.file_id,
                    caption=caption
                )
            # 11. Стикер
            elif message.sticker:
                saved_in_channel = await bot.send_sticker(
                    chat_id=await get_next_channel(),
                    sticker=message.sticker.file_id
                )
            # 12. Документ / Файл
            elif message.document:
                saved_in_channel = await bot.send_document(
                    chat_id=await get_next_channel(),
                    document=message.document.file_id,
                    caption=caption
                )
            # 13. Аудио (Музыкальный трек)
            elif message.audio:
                saved_in_channel = await bot.send_audio(
                    chat_id=await get_next_channel(),
                    audio=message.audio.file_id,
                    caption=caption
                )
            # 14. Неопознанный / новый тип
            else:
                print("Неопознаный тип сообщения")
                text = "Сообщение неизвестного типа (не удалось сохранить содержимое)"
                await save_msg((user_id, chat_id, msg_id, name, None, None, text, time))
                return
        except Exception as e:
            logging.exception(f"Не удалось отправить медиа в архивный канал: {e}")
            text = caption or "Медиафайл (не удалось сохранить в архив)"
            await save_msg((user_id, chat_id, msg_id, name, None, None, text, time))
            return

        await save_msg((user_id, chat_id, msg_id, name, str(saved_in_channel.chat.id), str(saved_in_channel.message_id), caption, time))


# сохраняет новое сообщение в messages
async def save_msg(data: tuple) -> None:
    async with aiosqlite.connect(MESSAGES_FILE_PATH) as db:

        await db.execute("""
            INSERT OR REPLACE INTO messages (user_id, chat_id, msg_id, name, channel_id, channel_msg_id, text, time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

        await db.commit()

async def get_msg(user_id: str, chat_id: str, msg_id: str) -> tuple | None:
    async with aiosqlite.connect(MESSAGES_FILE_PATH) as db:
        
        async with db.execute("""
            SELECT *
            FROM messages
            WHERE user_id = ? AND chat_id = ? AND msg_id = ?
        """, (user_id, chat_id, msg_id)) as buffer:
            
            msg = await buffer.fetchone()  # Достаем 1 строку
            if msg:
                return msg  # Возвращаем всю строку
            
            return None