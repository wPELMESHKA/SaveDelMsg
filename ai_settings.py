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
            async with session.post(AI_LOCAL_URL, json={"model": AI_MODEL, "system": AI_SYSTEM_PROMPT, "prompt": question, "stream": True, "keep_alive": -1}) as resp:
                async for line in resp.content:
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    full_text += chunk.get("response", "")

                    now = asyncio.get_event_loop().time()
                    diff = now - last_edit
                    is_done = chunk.get("done", False)

                    if (diff >= 1 or is_done):
                        last_edit = now
                        try:
                            await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=full_text, business_connection_id=message.business_connection_id)
                        except Exception as e:
                            if "message is not modified" in str(e).lower():
                                pass
                            else:
                                print(f"[Telegram Edit Error]: {e}")