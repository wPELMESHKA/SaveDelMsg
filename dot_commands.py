import random
from aiogram import Bot
from aiogram.types import Message
from db_msgs import _userID_by_connID
import asyncio
from config import(
    SPAM_DEFAULT_NUM,
    SPAM_DELAY_SECONDS,
    SPAM_MAX_NUM
)


active_spammers = set()

async def dot_commands(message: Message, bot):
    if not is_owner(message):
        return 
    # находиться ли юзер в спамерах
    owner_id = _userID_by_connID(message.business_connection_id)
    if owner_id in active_spammers:
        await del_dot_command(message, bot)
        return
    
    if message.text.startswith(".random"):
        await random_dot_command(message, bot)

    elif message.text.startswith(".gay"):
        await gay_dot_command(message, bot)

    elif message.text.startswith(".spam"):
        await spam_dot_command(message, bot, owner_id)
    
    return



# .random
async def random_dot_command(message: Message, bot: Bot):
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

    # 3. Удаляем исходное сообщение владельца (".random")
    await del_dot_command(message, bot)
    
    # 4. Отправляем новое сообщение в этот же бизнес-чат
    await message.answer(f"Мне выпало число: <b>{random_num}</b>", parse_mode="HTML")
    return


# .gay
async def gay_dot_command(message: Message, bot: Bot):
    random_num = random.randint(0, 100)

    await del_dot_command(message, bot)

    await message.answer(f"🏳️‍🌈Я гей на <b>{random_num}%</b>🏳️‍🌈", parse_mode="HTML")
    return


# .spam
async def spam_dot_command(message: Message, bot: Bot, owner_id) -> bool:
    active_spammers.add(owner_id)
    try:
        args = message.text.split(maxsplit=2)
        spam_num = SPAM_DEFAULT_NUM
        text_to_send = ""

        await del_dot_command(message, bot)

        if len(args) == 1:
            await message.answer("⚠️ Использование: \n<code>.spam [кол-во] [текст]</code>", parse_mode="HTML")
            return


        elif len(args) == 2:
            text_to_send = args[1]
            spam_num = SPAM_DEFAULT_NUM


        elif len(args) == 3:
            try:
                spam_num = int(args[1])

                # Если количество < 1 или больше максимума — выводим предупреждение
                if spam_num < 1 or spam_num > SPAM_MAX_NUM:
                    await message.answer("⚠️ Использование: \n<code>.spam [кол-во] [текст]</code>", parse_mode="HTML")
                    return
                
                text_to_send = args[2]

            except ValueError:
                # Если первый аргумент не число (например, ".spam привет мир")
                text_to_send = f"{args[1]} {args[2]}"
                spam_num = SPAM_DEFAULT_NUM


        # Цикл отправки
        for _ in range(spam_num):
            await message.answer(text_to_send)
            await asyncio.sleep(SPAM_DELAY_SECONDS)
    finally:
        active_spammers.discard(owner_id)

    return
    



def is_owner(message):
    owner_id = _userID_by_connID(message.business_connection_id)
    if not owner_id or not message.from_user:
        return False
    if str(message.from_user.id) != owner_id:
        return False
    return True



async def del_dot_command(message: Message, bot: Bot):
    try:
        await bot.delete_business_messages(
            business_connection_id=message.business_connection_id,
            message_ids=[message.message_id]
            )
        return
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        return