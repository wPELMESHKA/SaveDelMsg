from aiogram import Bot
from aiogram.types import Message
import json
import os
from config import(
    HISTORY_DIR, 
    CHANNELS_ARCHIVE_IDS
)
from db_conns import(
    # функция загрузки информации из файла
    load_connections
)

channel = 0
def next_channel(channel_num):
    channel_num += 1
    if channel_num >= len(CHANNELS_ARCHIVE_IDS):
        channel_num = 0
    return channel_num


# проверка на все типы сообщений
async def save_msg(message: Message, bot: Bot):
    global channel
    # получаем айди владельца акаунта через вспомогательную функцию
    userID = _userID_by_connID(message.business_connection_id)
    if userID is None:
        return


    # создаем папку если ее еще нету 
    os.makedirs(os.path.join(HISTORY_DIR, userID), exist_ok=True)

    # ID собеседника
    chat_id: int = message.chat.id
    # ID сообщения
    msg_id: int = message.message_id
    # Подпись к фото или видео (будет str или None)
    caption = message.caption
    


    # 1. Обычный текст
    if message.text:
        data = load_data(userID, chat_id)
        data[str(msg_id)] = {
            "channel_id":       None,
            "channel_msg_id":   None,
            "text":             message.text
        }
        with open(os.path.join(HISTORY_DIR, userID, f"{chat_id}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    # 2. Интерактивный  эмодзи (🎲/🎯/🏀/⚽/🎳/🎰)
    elif message.dice:
        data = load_data(userID, chat_id)
        data[str(msg_id)] = {
                "channel_id":       None,
                "channel_msg_id":   None,
                "text":             f"Интерактивный эмодзи: {message.dice.emoji} (Значение: {message.dice.value})"
            }
        with open(os.path.join(HISTORY_DIR, userID, f"{chat_id}.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
        
    # 3. Геолокация
    elif message.location:
        data = load_data(userID, chat_id)
        data[str(msg_id)] = {
                "channel_id":       None,
                "channel_msg_id":   None,
                "text": (
                    f"Геолокация:\n"
                    f"Координата Х (Долгота): {message.location.longitude}\n"
                    f"Координата Y (Широта): {message.location.latitude}\n"
                    f'<a href="https://maps.google.com/?q={message.location.latitude},{message.location.longitude}">Открыть на Google картах</a>'
                )        
            }
        with open(os.path.join(HISTORY_DIR, userID, f"{chat_id}.json"), "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)


    # 4. Контакт (Номер телефона)
    elif message.contact:
        data = load_data(userID, chat_id)
        text_contact = ( 
            f"Имя контакта: {message.contact.full_name}\n"
            f"Номер телефона контакта: {message.contact.phone_number}\n"
        )
        if message.contact.user_id:
            text_contact += f'<a href="tg://user?id={message.contact.user_id}">Открыть профиль в Telegram</a>'
        data[str(msg_id)] = {
                "channel_id":       None,
                "channel_msg_id":   None,
                "text":             text_contact
            }
        with open(os.path.join(HISTORY_DIR, userID, f"{chat_id}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
    # 5. Фотография
    elif message.photo:
        # Отправляем в канал по file_id
        saved_in_channel = await bot.send_photo(
            chat_id=CHANNELS_ARCHIVE_IDS[channel],
            photo=message.photo[-1].file_id, # Самое лучшее качество,
            caption=caption
        )
        _rewrite_data(userID, chat_id, saved_in_channel, caption, msg_id)

    # 6. Видео
    elif message.video:
        saved_in_channel = await bot.send_video(
            chat_id=CHANNELS_ARCHIVE_IDS[channel],
            video=message.video.file_id,
            caption=caption
        )
        _rewrite_data(userID, chat_id, saved_in_channel, caption, msg_id)

    # 7. Голосовое сообщение (Voice)
    elif message.voice:
        saved_in_channel = await bot.send_voice(
            chat_id=CHANNELS_ARCHIVE_IDS[channel],
            voice=message.voice.file_id
        )
        _rewrite_data(userID, chat_id, saved_in_channel, caption, msg_id)

    # 8. Видеосообщение (Кружочек / Video Note)
    elif message.video_note:
        saved_in_channel = await bot.send_video_note(
            chat_id=CHANNELS_ARCHIVE_IDS[channel],
            video_note=message.video_note.file_id
        )
        _rewrite_data(userID, chat_id, saved_in_channel, caption, msg_id)
        
    # 9. ГИФ-анимация (Animation)
    elif message.animation:
        saved_in_channel = await bot.send_animation(
            chat_id=CHANNELS_ARCHIVE_IDS[channel],
            animation=message.animation.file_id,
            caption=caption
        )
        _rewrite_data(userID, chat_id, saved_in_channel, caption, msg_id)
        
    # 10. Стикер
    elif message.sticker:
        saved_in_channel = await bot.send_sticker(
            chat_id=CHANNELS_ARCHIVE_IDS[channel],
            sticker=message.sticker.file_id
        )
        _rewrite_data(userID, chat_id, saved_in_channel, caption, msg_id)

    # 11. Документ / Файл
    elif message.document:
        saved_in_channel = await bot.send_document(
            chat_id=CHANNELS_ARCHIVE_IDS[channel],
            document=message.document.file_id,
            caption=caption
        )
        _rewrite_data(userID, chat_id, saved_in_channel, caption, msg_id)

    # 12. Аудио (Музыкальный трек)
    elif message.audio:
        saved_in_channel = await bot.send_audio(
            chat_id=CHANNELS_ARCHIVE_IDS[channel],
            audio=message.audio.file_id,
            caption=caption
        )
        _rewrite_data(userID, chat_id, saved_in_channel, caption, msg_id)

    # 13. Неопознанный / новый тип
    else:
        pass

def _userID_by_connID(conn):
    data = load_connections()
    if conn not in data:
        return None
    return data[conn]


# функция загрузки данных из файла
def load_data(user_id, chat_id) -> dict:
    # если файла нету возращаем пустой список
    if not os.path.exists(os.path.join(HISTORY_DIR, user_id, f"{chat_id}.json")):
        return {}
    # открываем файл в режиме чтения ("r"), с кодировкой utf-8
    with open(os.path.join(HISTORY_DIR, user_id, f"{chat_id}.json"), "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _rewrite_data(userID, chat_id, saved_in_channel, caption, msg_id):
    global channel
    data = load_data(userID, chat_id)
    data[str(msg_id)] = {
        "channel_id":       CHANNELS_ARCHIVE_IDS[channel],
        "channel_msg_id":   saved_in_channel.message_id,
        "text":             caption
    }
    with open(os.path.join(HISTORY_DIR, userID, f"{chat_id}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    channel = next_channel(channel)
     