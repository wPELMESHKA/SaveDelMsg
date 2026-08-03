from groq import AsyncGroq
from html import escape
from config import(
    GROQ_API_TOKEN,
    GROQ_MODELS,
    GROQ_SYSTEM_PROMT
)
import asyncio

client = AsyncGroq(api_key=GROQ_API_TOKEN)


model_num = 0
model_lock = asyncio.Lock()
async def get_next_model() -> str:
    global model_num
    async with model_lock:
        chosen_model = GROQ_MODELS[model_num]
        model_num = (model_num + 1) % len(GROQ_MODELS)
        return chosen_model

async def get_answer(question: str):
    question_and_promt = [{
            "role": "system",
            "content": GROQ_SYSTEM_PROMT
        },
        {
            "role": "user",
            "content": escape(question)
        }]


    response = await client.chat.completions.create(
        model=await get_next_model(),
        messages=question_and_promt
    )

    return response.choices[0].message.content