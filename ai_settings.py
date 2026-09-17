import asyncio
import json
import time
import aiohttp

from config import (
    AI_SYSTEM_PROMPT,
    AI_MODEL,
    AI_LOCAL_URL
)

lock = asyncio.Lock()

async def get_ai_answer(bot, message, question):
    last_sended_text = ""
    text_to_send = ""
    last_edit = 0.0
    async with lock:
        async with aiohttp.ClientSession() as session:
            async with session.post(AI_LOCAL_URL, json={"model": AI_MODEL, "system": AI_SYSTEM_PROMPT, "prompt": question, "stream": True, "keep_alive": -1}) as resp:
                async for line in resp.content:
                    # удаляем пустые строки в ответе ollama (не сам текст ответа нейронки), чтобы избежать ошибок при парсинге JSON
                    if not line.strip():
                        continue
                    # превращаем строку в словарь Python
                    try:
                        chunk = json.loads(line)
                    except Exception as e:
                        print(f"[JSON Parse Error]: {e}\n\nLine: {line.decode('utf-8')}")
                        continue

                    new_token = chunk.get("response", "")

                    # проверяем пришел ли текст или какая то пустая строка
                    if new_token:
                        text_to_send += new_token

                        # если от нейронки пришел пробел или перенос строки, просто сохраняем в text_to_send,
                        # что б не вызвать ошибку телеграма "текст не изменился"
                        if text_to_send.strip() == last_sended_text:
                            continue

                        # если реально пришел какой то новый текст, проверяем прошла ли секунда с последнего редактирования, 
                        # что б не вызвать ошибку телеграма "текст не изменился" и не спамить слишком часто
                        elif time.monotonic() - last_edit >= 1.0:
                            try:
                                await bot.edit_message_text(
                                    chat_id=message.chat.id, 
                                    message_id=message.message_id, 
                                    text=text_to_send.strip(), 
                                    business_connection_id=message.business_connection_id
                                )
                                last_edit = time.monotonic()
                                last_sended_text = text_to_send.strip()
                            except Exception as e:
                                print(f"[Telegram Edit Error]: {e}")

                # отправляем оставшийся текст после окончания потока
                if text_to_send.strip() != last_sended_text.strip():

                    # если прошло меньше секунды с последнего редактирования, ждем оставшееся время
                    if time.monotonic() - last_edit < 1.0:
                        await asyncio.sleep(1.0 - (time.monotonic() - last_edit))

                    try:
                        await bot.edit_message_text(
                            chat_id=message.chat.id, 
                            message_id=message.message_id, 
                            text=text_to_send.strip(), 
                            business_connection_id=message.business_connection_id
                        )
                    except Exception as e:
                        print(f"[Telegram Edit Error]: {e}")