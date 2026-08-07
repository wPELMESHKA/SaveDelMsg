from html import escape
import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import Message

from config import (
    DATA_FOLDER,
    CHANNELS_ARCHIVE_IDS
)
from db_conns import (
    # функция загрузки информации из файла
    load_connections
)


# словарь с локами на .json файлы
file_locks = {}

channel = 0
channel_lock = asyncio.Lock()
async def get_next_channel() -> str:
    # берет текущий канал и переключает на следуюющий с локом
    global channel
    async with channel_lock:
        chosen_channel = CHANNELS_ARCHIVE_IDS[channel]
        channel = (channel + 1) % len(CHANNELS_ARCHIVE_IDS)
        return chosen_channel


# проверка на все типы сообщений
async def save_msg(message: Message, bot: Bot):
    # получаем айди владельца акаунта через вспомогательную функцию
    userID = _userID_by_connID(message.business_connection_id)
    if userID is None:
        return

    # когда в личку пишут от имени канала то message.from_user.id вообще не будет и код упадет 
    if message.from_user:
        if userID == str(message.from_user.id):
            return
        else: 
            partner_name = message.from_user.full_name
    else:
        return

    # создаем папку если ее еще нету 
    os.makedirs(os.path.join(DATA_FOLDER, userID), exist_ok=True)

    # ID собеседника
    chat_id: int = message.chat.id
    # ID сообщения
    msg_id: int = message.message_id
    # Подпись к фото или видео (будет str или None)
    caption = message.caption
    


    # 1. Обычный текст
    if message.text:
        new_msg = {
            "partner_name":     partner_name,
            "channel_id":       None,
            "channel_msg_id":   None,
            "text":             escape(message.text),
            "time":             datetime.now(timezone.utc).strftime("%H:%M %d.%m.%Y")
        }
        await _rewrite_data(userID, chat_id, msg_id, new_msg)


    # 2. Интерактивный  эмодзи (🎲/🎯/🏀/⚽/🎳/🎰)
    elif message.dice:
        new_msg = {
                "partner_name":     partner_name,
                "channel_id":       None,
                "channel_msg_id":   None,
                "text":             f"Интерактивный эмодзи: {message.dice.emoji} (Значение: {message.dice.value})",
                "time":             datetime.now(timezone.utc).strftime("%H:%M %d.%m.%Y")
            }
        await _rewrite_data(userID, chat_id, msg_id, new_msg)

        
    # 3. Геолокация
    elif message.location:
        new_msg = {
                "partner_name":     partner_name,
                "channel_id":       None,
                "channel_msg_id":   None,
                "text": (
                    f"Геолокация:\n"
                    f"Координата Х (Долгота): {message.location.longitude}\n"
                    f"Координата Y (Широта): {message.location.latitude}\n"
                    f'<a href="https://maps.google.com/?q={message.location.latitude},{message.location.longitude}">Открыть на Google картах</a>'
                ),
                "time":             datetime.now(timezone.utc).strftime("%H:%M %d.%m.%Y")   
            }
        await _rewrite_data(userID, chat_id, msg_id, new_msg)


    # 4. Контакт (Номер телефона)
    elif message.contact:
        new_msg = {
                "partner_name":     partner_name,
                "channel_id":       None,
                "channel_msg_id":   None,
                "text":(             
                    f"Имя контакта: {escape(message.contact.full_name)}\n"
                    f"Номер телефона контакта: {escape(message.contact.phone_number)}"
                    ),
                "time":             datetime.now(timezone.utc).strftime("%H:%M %d.%m.%Y")
            }
        await _rewrite_data(userID, chat_id, msg_id, new_msg)

    # 5. Место (Venue)
    elif message.venue:
        new_msg = {
                "partner_name":     partner_name,
                "channel_id":       None,
                "channel_msg_id":   None,
                "text": (
                    f"Место: {escape(message.venue.title)}\n"
                    f"Адрес: {escape(message.venue.address)}\n"
                    f'<a href="https://maps.google.com/?q={message.venue.location.latitude},{message.venue.location.longitude}">Открыть на Google картах</a>'
                    ),
                "time":             datetime.now(timezone.utc).strftime("%H:%M %d.%m.%Y")
            }
        await _rewrite_data(userID, chat_id, msg_id, new_msg)
 
 

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
                # даже для неизвестного типа сохраняем "заглушку",
                # чтобы событие удаления не потерялось молча
                new_msg = {
                    "partner_name":     partner_name,
                    "channel_id":       None,
                    "channel_msg_id":   None,
                    "text":             "Сообщение неизвестного типа (не удалось сохранить содержимое)",
                    "time":             datetime.now(timezone.utc).strftime("%H:%M %d.%m.%Y")
                }
                await _rewrite_data(userID, chat_id, msg_id, new_msg)
                return
        except Exception as e:
            logging.exception(f"Не удалось отправить медиа в архивный канал: {e}")
            # сохраняем запись без архивной копии, чтобы хотя бы факт
            # сообщения (и его последующее удаление) не потерялся
            new_msg = {
                "partner_name":     partner_name,
                "channel_id":       None,
                "channel_msg_id":   None,
                "text":             (caption or "Медиафайл (не удалось сохранить в архив)"),
                "time":             datetime.now(timezone.utc).strftime("%H:%M %d.%m.%Y")
            }
            await _rewrite_data(userID, chat_id, msg_id, new_msg)
            return


        new_msg = {
            "partner_name":     partner_name,
            "channel_id":       saved_in_channel.chat.id,
            "channel_msg_id":   saved_in_channel.message_id,
            "text":             caption,
            "time":             datetime.now(timezone.utc).strftime("%H:%M %d.%m.%Y")
            }
        await _rewrite_data(userID, chat_id, msg_id, new_msg)




def _userID_by_connID(conn):
    data = load_connections()
    if conn not in data:
        return None
    return data[conn]




# функция загрузки данных из файла
def load_data(user_id, chat_id) -> dict:
    # если файла нету возращаем пустой список
    if not os.path.exists(os.path.join(DATA_FOLDER, user_id, f"{chat_id}.json")):
        return {}
    # открываем файл в режиме чтения ("r"), с кодировкой utf-8
    with open(os.path.join(DATA_FOLDER, user_id, f"{chat_id}.json"), "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}




async def _rewrite_data(userID, chat_id, msg_id, new_msg):
    lock = get_file_lock(userID, chat_id)

    async with lock:
        temp_path = os.path.join(DATA_FOLDER, userID, f"_{chat_id}.json")
        main_path = os.path.join(DATA_FOLDER, userID, f"{chat_id}.json")


        # получаем данные с текущего файла
        data = load_data(userID, chat_id)

        # добавляем в словарь новое сообщение
        data[str(msg_id)] = new_msg

        # сохраняем готовый файл
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # удаляет main_path если он был, переносит файл из путя temp_path в main_path
        os.replace(temp_path, main_path)




def get_file_lock(user_id: str, chat_id: int) -> asyncio.Lock:
    # получаем лок для конкретного чата
    key = f"{user_id}_{chat_id}"
    if key not in file_locks:
        file_locks[key] = asyncio.Lock()
    return file_locks[key]