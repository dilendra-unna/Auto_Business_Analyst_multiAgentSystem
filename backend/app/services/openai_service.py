# app/services/openai_service.py

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load .env from the backend root (works regardless of cwd)
load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

async def generate(system_prompt: str, user_prompt: str) -> str:

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return response.choices[0].message.content
