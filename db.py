import json
import os
from config import(
    DB_FILE,
    HISTORY_DIR
)


# помогает сделать правильный путь к файлу: на Windows HISTORY_DIR\connections.json, на Linux HISTORY_DIR/connections.json
# CONNECTIONS_PATH = os.path.join(HISTORY_DIR, "connections.json")

# функция загрузки данных из файла
def load_connections() -> dict:
    # если файла нету возращаем пустой список
    if not os.path.exists(os.path.join(HISTORY_DIR, "connections.json")):
        return {}
    # открываем файл в режиме чтения ("r"), с кодировкой utf-8
    with open(os.path.join(HISTORY_DIR, "connections.json"), "r", encoding="utf-8") as f:
        return json.load(f)

# функция обновления данных в фалйе
def update_connections_data(conn_id: str, user_id: int) -> None:
    # загружаем список из файла
    data = load_connections()
    # добавляем/обновляем пару
    data[str(user_id)] = conn_id
    # перезаписываем весь словарь в файл
    with open(os.path.join(HISTORY_DIR, "connections.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    