from typing import *
import os
import tiktoken


def _getkey(key: Optional[str] = None):
    return key or os.environ["OPENAI_API_KEY"]


def chat(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    api_key: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> str:
    import openai

    api_key = _getkey(api_key)
    return openai.ChatCompletion.create(
        model=model, messages=messages, api_key=api_key, max_tokens=max_tokens
    )["choices"][0]["message"]["content"]


def count_tokens(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> int:
    tokens_per_message, tokens_per_name = {"gpt-3.5-turbo": (4, -1), "gpt-4": (3, 1)}[
        model
    ]
    enc = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(enc.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens


def get_token_limit(model: str = "gpt-3.5-turbo") -> int:
    return {
        "gpt-3.5-turbo": 4000,
        "gpt-4": 8000,
    }[model]
