import os
from dotenv import load_dotenv

load_dotenv()

BOT_API_TOKEN = os.getenv("BOT_API_TOKEN")

# несколько архивных каналов через запятую в .env — распределяем медиа по кругу,
# чтобы не упираться в лимит 1 сообщение/сек на один канал
CHANNELS_ARCHIVE_IDS = []

# код который разделяет строку с запятыми на несколько елементов в списке
archive_channel_ids_str = os.getenv("CHANNELS_ARCHIVE_IDS", "").replace(" ", "")
i = 0
while i < len(archive_channel_ids_str):
    if archive_channel_ids_str[i] == ",":
        CHANNELS_ARCHIVE_IDS.append(archive_channel_ids_str[:i])
        archive_channel_ids_str = archive_channel_ids_str[i + 1:]
        i = 0
    else:
        i += 1
CHANNELS_ARCHIVE_IDS.append(archive_channel_ids_str)



# сколько удалённых сообщений показывать за раз (остальные — одной строкой "ещё удалено X")
DELETED_MESSAGES_SHOWN = 10

# True  — показывать в чате и те сообщения, что удалил сам владелец аккаунта,
#         плюс добавлять строку "Сообщение удалил <ссылка>"
# False — показывать только удаления собеседника, без строки "Сообщение удалил"
SHOW_USER_DELETED_MESSAGES = False

# Папка, где хранятся файлы истории (по одному json-файлу на chat_id + connections.json)
HISTORY_DIR = "history"

DB_FILE = "connections.json"