import random
from aiogram import Bot
from aiogram.types import Message
from db_msgs import _userID_by_connID
import asyncio

async def dot_commands(message: Message, bot):
    if not is_owner(message):
        return 

    if message.text.startswith(".random"):
        return await random_dot_command(message, bot)

    elif message.text.startswith(".gay"):
        return await gay_dot_command(message, bot)

    elif message.text.startswith(".spam"):
        return await spam_dot_command(message, bot)
    
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
    return True


# .gay
async def gay_dot_command(message: Message, bot: Bot):
    random_num = random.randint(0, 100)

    await del_dot_command(message, bot)

    await message.answer(f"🏳️‍🌈Я гей на <b>{random_num}%</b>🏳️‍🌈", parse_mode="HTML")
    return True


# .spam
async def spam_dot_command(message: Message, bot: Bot):
    delay_seconds = 1.0
    args = message.text.split(maxsplit=2)
    spam_num = 5 # дефолтное значение
    if len(args) == 1:
        await del_dot_command(message, bot)
        await message.answer(f"⚠️ Использование: \n<code>.spam [кол-во] [текст]</code>", parse_mode="HTML")
        return

    elif len(args) == 2:
        await del_dot_command(message, bot)
        for i in range(spam_num):
            await message.answer(f"{args[1]}")
            await asyncio.sleep(delay_seconds)
        return True
    
    elif len(args) == 3:
        try:
            spam_num = int(args[1])

            if spam_num < 1:
                spam_num = 5 # дефолтное значение
                await del_dot_command(message, bot)
                for i in range(spam_num):
                    await message.answer(f"{args[1]} {args[2]}")
                    await asyncio.sleep(delay_seconds)
                return True

            else:
                await del_dot_command(message, bot)
                for i in range(spam_num):
                    await message.answer(f"{args[2]}")
                    await asyncio.sleep(delay_seconds)
                return True

        except ValueError:
            await del_dot_command(message, bot)
            for i in range(spam_num):
                await message.answer(f"{args[1]} {args[2]}")
                await asyncio.sleep(delay_seconds)
    



def is_owner(message):
    owner_id = _userID_by_connID(message.business_connection_id)
    if not owner_id or not message.from_user:
        return
    if str(message.from_user.id) != owner_id:
        return
    return True



async def del_dot_command(message: Message, bot: Bot):
    try:
        await bot.delete_business_messages(
            business_connection_id=message.business_connection_id,
            message_ids=[message.message_id]
            )
        return True
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        return