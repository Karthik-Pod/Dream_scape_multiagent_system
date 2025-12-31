import os
from groq import Groq
_client = None
def get_client():
    global _client

    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set in environment")

        _client = Groq(api_key=api_key)

    return _client


def call_llm(system_prompt: str, user_prompt: str) -> str:
    client = get_client()

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",   # text reasoning model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()
