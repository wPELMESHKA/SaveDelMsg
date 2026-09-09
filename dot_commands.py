import random
import asyncio
from html import escape

from aiogram import Bot
from aiogram.types import Message
import aiohttp

from db_conns import (
    get_user_id_by_conn_id
)
from config import (
    SPAM_DEFAULT_NUM,
    SPAM_MAX_NUM,
    BELOW_ZALGO_SYMBOLS,
    ABOVE_ZALGO_SYMBOLS
)
from ai_settings import (
    get_ai_answer
)
from blacklist import (
    is_blacklisted
)


active_spammers = set()

async def dot_commands(message: Message, bot):
    """
    Основной диспетчер пользовательских команд, начинающихся с точки.
    
    Проверяет права владельца и статус блокировки, после чего вызывает
    соответствующий хэндлер для обработки команды.
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    """
    owner_id = await get_user_id_by_conn_id(message.business_connection_id)
    if not is_owner(message, owner_id):
        return

    # находиться ли юзер в спамерах
    if owner_id in active_spammers:
        return

    if is_blacklisted(owner_id):
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="⚠️ Вы находитесь в черном списке", business_connection_id=message.business_connection_id)
        return

    command_word = message.text.split()[0] or None
    
    for dot_command, handler in COMMANDS_WITH_HANDLERS.items():
        if command_word == dot_command:
            await handler(message, bot)
            return

    if command_word == ".spam":
        await spam_dot_command(message, bot, owner_id)
        return
    return




# .help
async def help_dot_command(message: Message, bot: Bot):
    """
    Обрабатывает команду .help и выводит список всех доступных команд.
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    """
    if message.text != ".help":
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f"⚠️ Для данной команды аргументы не требуются", business_connection_id=message.business_connection_id)
        return

    await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=
        f"<b>🛠 Список доступных команд:</b>\n\n"
        "• <code>.help</code> — Показать это меню с инструкцией\n"
        "• <code>.random [мин] [макс]</code> — Число в заданном диапазоне (по умолчанию 0, 100)\n"
        "• <code>.gay</code> — Узнать свой уровень гейства\n"
        "• <code>.coin</code> — Подбросить монетку\n"
        "• <code>.reg [текст]</code> — Сделать текст СлУчАйНыМ рЕгИсТрОм\n"
        "• <code>.zalgo [текст]</code> — Сделать текст сломанным (лимит символов 1000)\n"
        "• <code>.spam [кол-во] [текст]</code> — Спам текстом 1 сообщение/с (по умолчанию 5 раз, максимум 50)\n"
        "• <code>.ai [текст]</code> — Задать вопрос ИИ без цензуры\n"
        "• <code>.tt [ссылка на TikTok]</code> — Отправить видео с TikTok без водяного знака\n",
        parse_mode="HTML",
        business_connection_id=message.business_connection_id
        )
    return


# .random
async def random_dot_command(message: Message, bot: Bot):
    """
    Генерирует и отправляет случайное число в заданном диапазоне (по умолчанию 0-100).
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    """
    # 1. Парсим аргументы (например ".random 0 100" станет [".random", "1", "100"])
    args = message.text.split()
    min_val, max_val = 0, 100  # Значения по умолчанию
    
    if len(args) == 3:
        try:
            val1 = int(args[1])
            val2 = int(args[2])
            min_val, max_val = min(val1, val2), max(val1, val2)
        except ValueError:
            pass  # Переданы не числа, остаются 0 и 100

    # 2. Генерируем случайное число
    random_num = random.randint(min_val, max_val)
    
    # 4. Отправляем новое сообщение в этот же бизнес-чат
    await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f"Мне выпало число: <b>{random_num}</b>", parse_mode="HTML", business_connection_id=message.business_connection_id)
    return


# .gay
async def gay_dot_command(message: Message, bot: Bot):
    """
    Вычисляет случайный процент для развлекательной команды .gay.
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    """
    random_num = random.randint(0, 100)
    if message.text != ".gay":
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f"⚠️ Для данной команды аргументы не требуются", business_connection_id=message.business_connection_id)
        return
    await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f"🏳️‍🌈Я гей на <b>{random_num}%</b>🏳️‍🌈", parse_mode="HTML", business_connection_id=message.business_connection_id)
    return


# .spam
async def spam_dot_command(message: Message, bot: Bot, owner_id) -> None:
    """
    Запускает цикличную отправку сообщений (спам) с заданным интервалом.
    
    Защищает от повторного запуска во время активности пользователя.
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    :param owner_id: ID владельца бизнес-чата.
    :return: None.
    """
    active_spammers.add(owner_id)
    try:
        args = message.text.split(maxsplit=2)
        spam_num = SPAM_DEFAULT_NUM
        text_to_send = ""

        

        if len(args) == 1:
            await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="⚠️ Использование: \n<code>.spam [кол-во] [текст]</code>", parse_mode="HTML", business_connection_id=message.business_connection_id)
            return


        elif len(args) == 2:
            text_to_send = args[1]
            spam_num = SPAM_DEFAULT_NUM


        elif len(args) == 3:
            try:
                spam_num = int(args[1])

                # Если количество < 1 или больше максимума — выводим предупреждение
                if spam_num < 1 or spam_num > SPAM_MAX_NUM:
                    await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="⚠️ Использование: \n<code>.spam [кол-во] [текст]</code>", parse_mode="HTML", business_connection_id=message.business_connection_id)
                    return
                
                text_to_send = args[2]

            except ValueError:
                # Если первый аргумент не число (например, ".spam привет мир")
                text_to_send = f"{args[1]} {args[2]}"
                spam_num = SPAM_DEFAULT_NUM


        # Цикл отправки
        for _ in range(spam_num):
            await bot.send_message(chat_id=message.chat.id, text=text_to_send, business_connection_id=message.business_connection_id)
            await asyncio.sleep(1.0)
    finally:
        active_spammers.discard(owner_id)

    return
    

# .reg
async def reg_dot_command(message: Message, bot: Bot):
    """
    Преобразует переданный текст в рандомный регистр символов (ЗаБоРчИкОм).
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    """
    args = message.text.split(maxsplit=1)
    
    if len(args) == 1:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="⚠️ Использование: \n<code>.reg [текст]</code>", parse_mode="HTML", business_connection_id=message.business_connection_id)
        return

    text_to_send = ""

    for i in args[1]:
        if random.randint(0, 1) == 0:
            text_to_send += i.upper()
        else:
            text_to_send += i.lower()

    await bot.send_message(chat_id=message.chat.id, text=text_to_send, business_connection_id=message.business_connection_id)
    return


# .zalgo
async def zalgo_dot_command(message: Message, bot: Bot):
    """
    Преобразует текст, добавляя к нему Zalgo-символы («зашумляет» текст).
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    """
    args = message.text.split(maxsplit=1)
    
    if len(args) == 1:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="⚠️ Использование: \n<code>.zalgo [текст]</code>", parse_mode="HTML", business_connection_id=message.business_connection_id)
        return
    if len(args[1]) > 1000:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="⚠️ Текст слишком длинный! (Максимум 1000 символов)", parse_mode="HTML", business_connection_id=message.business_connection_id)
        return
    text_to_send = ""
    for char in args[1]:
        text_to_send += (char + random.choice(ABOVE_ZALGO_SYMBOLS) + random.choice(BELOW_ZALGO_SYMBOLS))
    await bot.send_message(chat_id=message.chat.id, text=text_to_send, business_connection_id=message.business_connection_id)
    return


# .coin
async def coin_dot_command(message: Message, bot: Bot):
    """
    Симулирует подбрасывание монетки (Орел или Решка).
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    """
    if message.text != ".coin":
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f"⚠️ Для данной команды аргументы не требуются", business_connection_id=message.business_connection_id)
        return
    if random.randint(0, 1) == 0:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f"Результат подбрасывания:\n\n🦅 Выпал ОРЕЛ!", business_connection_id=message.business_connection_id)
    else:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f"Результат подбрасывания:\n\n🪙 Выпала РЕШКА!", business_connection_id=message.business_connection_id)
    return


# .ai
async def ai_dot_command(message: Message, bot: Bot):
    """
    Отправляет запрос к локальной нейросети и возвращает сгенерированный ответ.
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    """
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f"⚠️ Для данной команды требуется вопрос", business_connection_id=message.business_connection_id)
        return
    
    try:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f"⏳ Запрашиваю ответ нейросети...", business_connection_id=message.business_connection_id)
        await get_ai_answer(bot, message, args[1])
    except Exception as e:
        print(f"Ошибка нейросети: {e}")
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="⚠️ Ошибка при обращении к нейросети.", business_connection_id=message.business_connection_id)
        return


# .tt
async def tt_dot_command(message: Message, bot: Bot):
    """
    Получает прямую ссылку на видео TikTok через API TikWM.
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    """
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f"⚠️ Использование: \n<code>.tt [ссылка на TikTok]</code>", parse_mode="HTML", business_connection_id=message.business_connection_id)
        return

    temp_msg = await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="⏳ Запрашиваю видео из TikTok...", business_connection_id=message.business_connection_id)
    tt_data = await _get_tt_link(args[1])
    if not tt_data:
        try:
            await bot.delete_business_messages(
            business_connection_id=message.business_connection_id,
            message_ids=[temp_msg.message_id]
        )
        except Exception as e:
            print(f"Ошибка при удалении статусного сообщения: {e}")
        await bot.send_message(chat_id=message.chat.id, text="⚠️ Не удалось получить видео. Проверьте ссылку.", business_connection_id=message.business_connection_id)
        return

    tiktok_link, title = tt_data
    caption = f"Описание видео: {escape(title)}\n<a href='{tiktok_link}'>Прямая ссылка на mp4 без водяного знака</a>"

    try:
        await bot.delete_business_messages(
            business_connection_id=message.business_connection_id,
            message_ids=[temp_msg.message_id]
        )
    except Exception as e:
        print(f"Ошибка при удалении статусного сообщения: {e}")

    try:
        await bot.send_video(
            chat_id=message.chat.id,
            video=tiktok_link,
            caption=caption,
            parse_mode="HTML",
            business_connection_id=message.business_connection_id
        )
    except Exception as e:
        print(f"Ошибка при отправке видео: {e}")
        await message.answer(
            f"⚠️ Не удалось отправить видео. Возможно оно приватное или больше 20 мб.\n"
            f"<a href='{tiktok_link}'>Прямая ссылка на скачивание</a>", parse_mode="HTML"
        )



def is_owner(message, owner_id):
    if not owner_id or not message.from_user:
        return False
    if str(message.from_user.id) != str(owner_id):
        return False
    return True



async def del_dot_command(message: Message, bot: Bot):
    """
    Удаляет исходное сообщение с бизнес-командой пользователя.
    
    :param message: Объект входящего сообщения Telegram.
    :param bot: Экземпляр бота Aiogram.
    """
    try:
        await bot.delete_business_messages(
            business_connection_id=message.business_connection_id,
            message_ids=[message.message_id]
            )
        return
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        return

async def _get_tt_link(tiktok_url: str) -> tuple[str, str] | None:
    """
    Получает прямую ссылку на видео TikTok через API TikWM.
    
    :param tiktok_url: Ссылка на видео TikTok.
    :return: Кортеж из прямой ссылки на mp4 и описания видео или None в случае ошибки.
    """
    api_url = "https://www.tikwm.com/api/"
    payload = {"url": tiktok_url, "hd": 1}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(api_url, data=payload) as response:
                res_data = await response.json()

                if res_data.get("code") == 0:
                    video_url = res_data["data"]["play"]
                    if video_url.startswith("/"):
                        video_url = "https://www.tikwm.com" + video_url
                    return video_url, res_data['data'].get('title', 'Без описания')
                else:
                    print(
                        f"❌ Ошибка API: {res_data.get('msg', 'Неизвестная ошибка')}"
                    )
                    return None
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            return None

COMMANDS_WITH_HANDLERS ={
    ".help": help_dot_command,
    ".random": random_dot_command,
    ".gay": gay_dot_command,
    ".reg": reg_dot_command,
    ".zalgo": zalgo_dot_command,
    ".coin": coin_dot_command,
    ".ai": ai_dot_command,
    ".tt": tt_dot_command,
}