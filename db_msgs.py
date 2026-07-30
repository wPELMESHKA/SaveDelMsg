from aiogram.types import Message
import json
import os
from config import(
    HISTORY_DIR
)
from db_conns import(
    # функция загрузки информации из файла
    load_connections
)

# проверка на все типы сообщений
async def save_msg(message: Message):
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
            "type": "text",
            "file": None,
            "text": message.text
        }
        with open(os.path.join(HISTORY_DIR, userID, f"{chat_id}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    # 2. Фотография
    elif message.photo:
        # photo = message.photo[-1] # Самое лучшее качество
        pass
    # 3. Видео
    elif message.video:
        pass

    # 4. Голосовое сообщение (Voice)
    elif message.voice:
        pass

    # 5. Видеосообщение (Кружочек / Video Note)
    elif message.video_note:
        pass

    # 6. ГИФ-анимация (Animation)
    elif message.animation:
        pass

    # 7. Стикер
    elif message.sticker:
        pass

    # 8. Документ / Файл
    elif message.document:
        pass
    # 9. Аудио (Музыкальный трек)
    elif message.audio:
        pass

    # 10. Интерактивный кубик / эмодзи (Dice)
    elif message.dice:
        pass

    # 11. Геолокация (Карта)
    elif message.location:
        pass

    # 12. Контакт (Номер телефона)
    elif message.contact:
        pass

    # 13. Опрос (Poll)
    elif message.poll:
        pass

    # 14. Неопознанный / новый тип
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