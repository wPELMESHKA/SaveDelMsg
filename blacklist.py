import os
from config import(
    BLACKLIST_FILE_NAME, 
    DATA_FOLDER
)

cache = {"last_update_time": None, "blacklist_ids": set()}

def is_blacklisted(user_id):
    blacklist_path = os.path.join(DATA_FOLDER, f"{DATA_FOLDER}_sub_folder", BLACKLIST_FILE_NAME)

    if not os.path.exists(blacklist_path):
        print("Нету файла черного списка")
        return False

    last_update_time = os.path.getmtime(blacklist_path)

    # перечитываем файл только если он реально изменился
    if last_update_time != cache["last_update_time"]:
        with open(blacklist_path, "r", encoding="utf-8") as f:
            blacklist_ids = set()
            for line in f:
                if not line.strip():
                    continue
                else:
                    blacklist_ids.add(str(line.strip()))
        cache["last_update_time"] = last_update_time
        cache["blacklist_ids"] = blacklist_ids

    return str(user_id) in cache["blacklist_ids"]