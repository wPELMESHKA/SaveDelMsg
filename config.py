import os
from dotenv import load_dotenv

load_dotenv()

BOT_API_TOKEN = os.getenv("BOT_API_TOKEN")

# несколько архивных каналов через запятую в .env — распределяем медиа по кругу,
# чтобы не упираться в лимит 1 сообщение/сек на один канал
CHANNELS_ARCHIVE_IDS = []

# код который разделяет строку с запятыми на несколько елементов в списке
archive_channel_ids_str = os.getenv("CHANNELS_ARCHIVE_IDS", "").replace(" ", "")
if not archive_channel_ids_str:
    raise RuntimeError(
        "CHANNELS_ARCHIVE_IDS не задан в .env — укажи хотя бы один ID канала для архива медиа"
    )

i = 0
while i < len(archive_channel_ids_str):
    if archive_channel_ids_str[i] == ",":
        CHANNELS_ARCHIVE_IDS.append(archive_channel_ids_str[:i])
        archive_channel_ids_str = archive_channel_ids_str[i + 1:]
        i = 0
    else:
        i += 1
CHANNELS_ARCHIVE_IDS.append(archive_channel_ids_str)

GROQ_API_TOKEN = os.getenv("GROQ_API_TOKEN")

GROQ_MODELS = [
    "llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-120b", 
    "openai/gpt-oss-20b", "qwen/qwen3.6-27b"
    ]

GROQ_SYSTEM_PROMT = """Ты — "GLENT AI". Твои правила ответа:
1. Отвечай четко, по делу и понятно, без «воды» и гигантских текстов.
2. Используй легкий юмор и дружелюбный тон.
3. Оформляй ВСЕ ответы только в формате Telegram HTML.
4. РАЗРЕШЕНЫ ТОЛЬКО теги: <b>, <i>, <u>, <s>, <code>, <pre>.
5. КРИТИЧЕСКИ ВАЖНО: ЗАПРЕЩЕНО использовать теги <p>, <h1>, <h2>, <h3>, <div>, <br>, <ul>, <li> и любые другие веб-теги! Для абзацев используй обычный перенос строки. Не используй Markdown и никогда не обворачивай ответ в блоки кода (```html ... ```)."""
# сколько удалённых сообщений показывать за раз (остальные — одной строкой "ещё удалено X")
DELETED_MESSAGES_SHOWN = 10

# Папка, где хранятся файлы истории (по одному json-файлу на chat_id + connections.json)
HISTORY_DIR = "history"

DB_FILE = "connections.json"

SPAM_DELAY_SECONDS = 1.0

SPAM_DEFAULT_NUM = 5

SPAM_MAX_NUM = 50



# zalgo символы
ABOVE_ZALGO_SYMBOLS = [
    "\u0300", "\u0301", "\u0302", "\u0303", "\u0304", "\u0305", "\u0306", "\u0307", "\u0308", "\u0309",
    "\u030A", "\u030B", "\u030C", "\u030D", "\u030E", "\u030F", "\u0310", "\u0311", "\u0312", "\u0313",
    "\u0314", "\u0315", "\u031A", "\u033D", "\u033E", "\u033F", "\u0342", "\u0343", "\u0344", "\u0346",
    "\u034A", "\u034B", "\u034C", "\u0350", "\u0351", "\u0352", "\u0357", "\u0358", "\u035B", "\u0363",
    "\u0364", "\u0365", "\u0366", "\u0367", "\u0368", "\u0369", "\u036A", "\u036B", "\u036C", "\u036D"
]

BELOW_ZALGO_SYMBOLS = [
    "\u0316", "\u0317", "\u0318", "\u0319", "\u031C", "\u031D", "\u031E", "\u031F", "\u0320", "\u0324",
    "\u0325", "\u0326", "\u0329", "\u032A", "\u032B", "\u032C", "\u032D", "\u032E", "\u032F", "\u0330",
    "\u0331", "\u0332", "\u0333", "\u0339", "\u033A", "\u033B", "\u033C", "\u0345", "\u0347", "\u0348",
    "\u0349", "\u034D", "\u034E", "\u0353", "\u0354", "\u0355", "\u0356", "\u0359", "\u035A", "\u0323",
    "\u1DC0", "\u1DC1", "\u1DC2", "\u1DC3", "\u1DC4", "\u1DC5", "\u1DC6", "\u1DC7", "\u1DC8", "\u1DC9"
]
