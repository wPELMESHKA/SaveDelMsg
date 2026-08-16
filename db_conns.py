import json
import os
import asyncio

from aiogram import Bot

from config import(
    DB_FILE,
    DATA_FOLDER
)


# лок на файл connections.json (он один на весь бот, поэтому лок глобальный)
connections_lock = asyncio.Lock()

# функция загрузки данных из файла
def load_connections() -> dict:
    # если файла нету возращаем пустой список
    if not os.path.exists(os.path.join(DATA_FOLDER, f"{DATA_FOLDER}_sub_folder", DB_FILE)):
        return {}
    # открываем файл в режиме чтения ("r"), с кодировкой utf-8
    with open(os.path.join(DATA_FOLDER, f"{DATA_FOLDER}_sub_folder", DB_FILE), "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except  json.JSONDecodeError:
            # файл пустой или повреждён (например, бот упал во время записи)
            return {}


# добавляет подключение в connections.json, если бот включен
async def add_connection(conn_id: str, user_id: int) -> None:
    async with connections_lock:
        temp_path = os.path.join(DATA_FOLDER, f"{DATA_FOLDER}_sub_folder", f"_{DB_FILE}")
        main_path = os.path.join(DATA_FOLDER, f"{DATA_FOLDER}_sub_folder", DB_FILE)

        # загружаем cловарь из файла
        data = load_connections()

        # добавляем пару
        data[str(conn_id)] = str(user_id)

        # перезаписываем весь словарь в временный файл
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        os.replace(temp_path, main_path)


# удаляет подключение из connections.json, если бот отключен
async def remove_connection(conn_id: str) -> None:
    async with connections_lock:
        temp_path = os.path.join(DATA_FOLDER, f"{DATA_FOLDER}_sub_folder", f"_{DB_FILE}")
        main_path = os.path.join(DATA_FOLDER, f"{DATA_FOLDER}_sub_folder", DB_FILE)

        data = load_connections()

        conn_str = str(conn_id)
        if conn_str in data:
            del data[conn_str]

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            os.replace(temp_path, main_path)


async def restore_connection(conn_id, bot: Bot):
    try:
        conn_data = await bot.get_business_connection(business_connection_id=conn_id)
        await add_connection(conn_id, conn_data.user.id)
    except Exception as e:
        print(f"Ошибка при восстановлении подключения {conn_id}: {e}")