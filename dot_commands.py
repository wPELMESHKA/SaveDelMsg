import random
from aiogram import Bot
from aiogram.types import Message
from db_msgs import _userID_by_connID
import asyncio
from config import(
    SPAM_DEFAULT_NUM,
    SPAM_DELAY_SECONDS,
    SPAM_MAX_NUM,
    BELOW_ZALGO_SYMBOLS,
    ABOVE_ZALGO_SYMBOLS
)
from groq_settings import get_answer
from blacklist import is_blacklisted


active_spammers = set()

async def dot_commands(message: Message, bot):
    owner_id = _userID_by_connID(message.business_connection_id)
    if not is_owner(message, owner_id):
        return

    # находиться ли юзер в спамерах
    if owner_id in active_spammers:
        return

    if is_blacklisted(owner_id):
        await del_dot_command(message, bot)
        await message.answer("⚠️ Вы находитесь в черном списке")
        return
    
    for dot_command, handler in COMMANDS_WITH_HANDLERS.items():
        if message.text.startswith(dot_command):
            await del_dot_command(message, bot)
            await handler(message, bot)
            return

    if message.text.startswith(".spam"):
        await del_dot_command(message, bot)
        await spam_dot_command(message, bot, owner_id)
        return
    return




# .help
async def help_dot_command(message: Message, bot: Bot):
    if message.text != ".help":
        await message.answer(f"⚠️ Для данной команды аргументы не требуются")
        return

    await message.answer(
        f"<b>🛠 Список доступных команд:</b>\n\n"
        "• <code>.help</code> — Показать это меню с инструкцией\n"
        "• <code>.random [мин] [макс]</code> — Число в заданном диапазоне (по умолчанию 0, 100)\n"
        "• <code>.gay</code> — Узнать свой уровень гейства\n"
        "• <code>.coin</code> — Подбросить монетку\n"
        "• <code>.reg [текст]</code> — Сделать текст СлУчАйНыМ рЕгИсТрОм\n"
        "• <code>.zalgo [текст]</code> — Сделать текст сломанным (лимит символов 1000)\n"
        "• <code>.spam [кол-во] [текст]</code> — Спам текстом 1 сообщение/с (по умолчанию 5 раз, максимум 50)\n"
        "• <code>.ai [текст]</code> — Задать вопрос ИИ (лимит символов 200)",
        parse_mode="HTML"
        )
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
    
    
    # 4. Отправляем новое сообщение в этот же бизнес-чат
    await message.answer(f"Мне выпало число: <b>{random_num}</b>", parse_mode="HTML")
    return


# .gay
async def gay_dot_command(message: Message, bot: Bot):
    random_num = random.randint(0, 100)
    if message.text != ".gay":
        await message.answer(f"⚠️ Для данной команды аргументы не требуются")
        return
    await message.answer(f"🏳️‍🌈Я гей на <b>{random_num}%</b>🏳️‍🌈", parse_mode="HTML")
    return


# .spam
async def spam_dot_command(message: Message, bot: Bot, owner_id) -> bool:
    active_spammers.add(owner_id)
    try:
        args = message.text.split(maxsplit=2)
        spam_num = SPAM_DEFAULT_NUM
        text_to_send = ""

        

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
    

# .reg
async def reg_dot_command(message: Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    
    if len(args) == 1:
        await message.answer("⚠️ Использование: \n<code>.reg [текст]</code>", parse_mode="HTML")
        return

    text_to_send = ""

    for i in args[1]:
        if random.randint(0, 1) == 0:
            text_to_send += i.upper()
        else:
            text_to_send += i.lower()

    await message.answer(text_to_send)
    return


# .zalgo
async def zalgo_dot_command(message: Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    
    if len(args) == 1:
        await message.answer("⚠️ Использование: \n<code>.zalgo [текст]</code>", parse_mode="HTML")
        return
    if len(args[1]) > 1000:
        await message.answer("⚠️ Текст слишком длинный! (Максимум 1000 символов)", parse_mode="HTML")
        return
    text_to_send = ""
    for char in args[1]:
        text_to_send += (char + random.choice(ABOVE_ZALGO_SYMBOLS) + random.choice(BELOW_ZALGO_SYMBOLS))
    await message.answer(text_to_send)
    return


# .coin
async def coin_dot_command(message: Message, bot: Bot):
    
    if message.text != ".coin":
        await message.answer(f"⚠️ Для данной команды аргументы не требуются")
        return
    if random.randint(0, 1) == 0:
        await message.answer(f"Результат подбрасывания:\n\n🦅 Выпал ОРЕЛ!")
    else:
        await message.answer(f"Результат подбрасывания:\n\n🪙 Выпала РЕШКА!")
    return


# .ai
async def ai_dot_command(message: Message, bot: Bot):
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(f"⚠️ Для данной команды требуется вопрос")
        return
    
    if len(args[1]) > 200:
        await message.answer(f"⚠️ Максимальная длина вопроса 200 символов")
        return

    try:
        answer = await get_answer(args[1])
    except Exception as e:
        print(f"Ошибка API Groq: {e}")
        await message.answer("⚠️ Ошибка при обращении к нейросети.")
        return

    await message.answer(answer, parse_mode="HTML")


def is_owner(message, owner_id):
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


COMMANDS_WITH_HANDLERS ={
    ".help": help_dot_command,
    ".random": random_dot_command,
    ".gay": gay_dot_command,
    ".reg": reg_dot_command,
    ".zalgo": zalgo_dot_command,
    ".coin": coin_dot_command,
    ".ai": ai_dot_command,
}