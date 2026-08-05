from groq import AsyncGroq
from html import escape
import re
from config import(
    GROQ_API_TOKEN,
    GROQ_MODELS,
    GROQ_SYSTEM_PROMPT
)
import asyncio

client = AsyncGroq(api_key=GROQ_API_TOKEN)

ALLOWED_TAGS = "b|i|u|s|code|pre|tg-spoiler"



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
            "content": GROQ_SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": question
        }]


    response = await client.chat.completions.create(
        model=await get_next_model(),
        messages=question_and_promt
    )

    return clean_answer(response.choices[0].message.content)



def clean_answer(answer: str) -> str:
    # Удаляем <think> вместе со ВСОЙ внутренностью
    answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
    # На случай, если тег <think> открылся, но не был закрыт
    answer = re.sub(r'<think>.*', '', answer, flags=re.DOTALL).strip()

    answer = escape(answer)

    # &lt; = <
    # &gt; = >
    # . = любой символ
    # * = 0 или больше раз 
    # \1 = ссылка на то что нашлось в первых скобках
    tag_pattern = re.compile(
        rf"&lt;({ALLOWED_TAGS})&gt;(.*?)&lt;/\1&gt;",
        re.DOTALL,
    )

    # &quot; = "
    # + = 1 или больше раз
    # [^&] = любой символ кроме &
    link_pattern = re.compile(
        r'&lt;a href=&quot;(https?://.+?)&quot;&gt;(.*?)&lt;/a&gt;',
        re.DOTALL,
    )

    prev = None
    while prev != answer:
        prev = answer
        # tag_pattern.sub(функция, answer) — команда "найди все совпадения по шаблону tag_pattern внутри answer, 
        # и для каждого совпадения вызови эту функцию, а результат подставь на место найденного".
        answer = tag_pattern.sub(lambda tag_match: f"<{tag_match.group(1)}>{tag_match.group(2)}</{tag_match.group(1)}>", answer)
        answer = link_pattern.sub(lambda link_match: f'<a href="{link_match.group(1)}">{link_match.group(2)}</a>', answer)

    return answer