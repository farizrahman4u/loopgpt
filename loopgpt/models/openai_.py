from typing import *
from loopgpt.logger import logger
import tiktoken
import time
import os


def _getkey(key: Optional[str] = None):
    key = key or os.getenv("OPENAI_API_KEY")
    if key is None:
        raise ValueError(
            "OpenAI API Key not found. Please set the `OPENAI_API_KEY` environment variable. "
            "See https://github.com/farizrahman4u/loopgpt#-requirements for more details"
        )


def chat(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    api_key: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.8,
) -> str:
    import openai
    from openai.error import RateLimitError

    api_key = _getkey(api_key)
    num_retries = 3
    for _ in range(num_retries):
        try:
            return openai.ChatCompletion.create(
                model=model,
                messages=messages,
                api_key=api_key,
                max_tokens=max_tokens,
                temperature=temperature,
            )["choices"][0]["message"]["content"]
        except RateLimitError:
            logger.warn("Rate limit exceeded. Retrying after 20 seconds.")
            time.sleep(20)
            continue


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
