from typing import *
import openai
import os


def _getkey(key: Optional[str] = None):
    return key or os.environ["OPENAI_API_KEY"]


def chat(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    api_key: Optional[str] = None,
    max_tokens: Optional[int] = None,
):
    api_key = _getkey(api_key)
    return openai.ChatCompletion.create(
        model=model, messages=messages, api_key=api_key, max_tokens=max_tokens
    )["choices"][0]["message"]["content"]
