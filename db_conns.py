import os

from aiogram import Bot
import aiosqlite

from config import(
    DATA_FOLDER
)

CONNECTIONS_FILE_PATH = os.path.join(DATA_FOLDER, "connections.db")



# инициализирует таблицу если она не существует
async def init_connections_table():
    async with aiosqlite.connect(CONNECTIONS_FILE_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                conn_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL
            )
        """)

        await db.commit()



# добавляет подключение в connections
async def add_connection(conn_id: str, user_id: int) -> None:
    async with aiosqlite.connect(CONNECTIONS_FILE_PATH) as db:

        await db.execute("""
            INSERT OR REPLACE INTO connections (conn_id, user_id)
            VALUES (?, ?)
        """, (str(conn_id), str(user_id)))

        await db.commit()



# удаляет подключение из connections, если бот отключен
async def remove_connection(conn_id: str) -> None:
    async with aiosqlite.connect(CONNECTIONS_FILE_PATH) as db:

        await db.execute("""
            DELETE FROM connections 
            WHERE conn_id = ?
        """, (str(conn_id),))

        await db.commit()



# отправляет запрос к API Telegram для получения информации о подключении и добавляет его в connections
async def restore_connection(conn_id, bot: Bot) -> None:
    try:
        conn_data = await bot.get_business_connection(business_connection_id=conn_id)
        await add_connection(conn_id, conn_data.user.id)
    except Exception as e:
        print(f"Ошибка при восстановлении подключения {conn_id}: {e}")



# получает user_id по conn_id из connections
async def get_user_id_by_conn_id(conn_id: str) -> str | None:
    if not conn_id:
        return None
    async with aiosqlite.connect(CONNECTIONS_FILE_PATH) as db:

        async with db.execute("""
            SELECT user_id 
            FROM connections 
            WHERE conn_id = ?
        """, (conn_id,)) as buffer:
            
            msg = await buffer.fetchone()  # Достаем 1 строку
            if msg:
                return str(msg[0])  # Возвращаем user_id
            
            return None