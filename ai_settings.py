import asyncio
import json

import aiohttp

from config import (
    AI_SYSTEM_PROMPT,
    AI_MODEL,
    AI_LOCAL_URL
)

lock = asyncio.Lock()



async def get_ai_answer(bot, message, question):
    full_text = ""
    last_edit = 0
    async with lock:
        async with aiohttp.ClientSession() as session:
            async with session.post(AI_LOCAL_URL, json={"model": AI_MODEL, "system": AI_SYSTEM_PROMPT, "prompt": question, "stream": True}) as resp:
                async for line in resp.content:
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    full_text += chunk.get("response", "")

                    now = asyncio.get_event_loop().time()
                    if now - last_edit >= 1:
                        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=full_text, business_connection_id=message.business_connection_id)
                        last_edit = now

                    if chunk.get("done"):
                        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=full_text, business_connection_id=message.business_connection_id)



# def clean_answer(answer: str) -> str:
#     # Удаляем <think> вместе со ВСОЙ внутренностью
#     answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
#     # На случай, если тег <think> открылся, но не был закрыт
#     answer = re.sub(r'<think>.*', '', answer, flags=re.DOTALL).strip()

#     answer = escape(answer)

#     # &lt; = <
#     # &gt; = >
#     # . = любой символ
#     # * = 0 или больше раз 
#     # \1 = ссылка на то что нашлось в первых скобках
#     tag_pattern = re.compile(
#         rf"&lt;({ALLOWED_TAGS})&gt;(.*?)&lt;/\1&gt;",
#         re.DOTALL,
#     )

#     # &quot; = "
#     # + = 1 или больше раз
#     # [^&] = любой символ кроме &
#     link_pattern = re.compile(
#         r'&lt;a href=&quot;(https?://.+?)&quot;&gt;(.*?)&lt;/a&gt;',
#         re.DOTALL,
#     )

#     prev = None
#     while prev != answer:
#         prev = answer
#         # tag_pattern.sub(функция, answer) — команда "найди все совпадения по шаблону tag_pattern внутри answer, 
#         # и для каждого совпадения вызови эту функцию, а результат подставь на место найденного".
#         answer = tag_pattern.sub(lambda tag_match: f"<{tag_match.group(1)}>{tag_match.group(2)}</{tag_match.group(1)}>", answer)
#         answer = link_pattern.sub(lambda link_match: f'<a href="{link_match.group(1)}">{link_match.group(2)}</a>', answer)

#     return answer