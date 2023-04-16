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
):
    import openai

    api_key = _getkey(api_key)
    return openai.ChatCompletion.create(
        model=model, messages=messages, api_key=api_key, max_tokens=max_tokens
    )["choices"][0]["message"]["content"]


def count_tokens(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo"):
    if model == "gpt-3.5-turbo":
        tokens_per_message = 4
        tokens_per_name = -1
    elif model == "gpt-4":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(f"Model not supported: {model}")
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
