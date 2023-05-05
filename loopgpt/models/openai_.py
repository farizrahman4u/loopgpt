from typing import *
from loopgpt.logger import logger
from loopgpt.models.base import BaseModel

import tiktoken
import time
import os


def _getkey(key: Optional[str] = None):
    key = key or os.getenv("OPENAI_API_KEY")
    if key is None:
        raise ValueError(
            f"OpenAI API Key not found in the current working directory: {os.getcwd()}. "
            "Please set the `OPENAI_API_KEY` environment variable or add it to `.env`. "
            "See https://github.com/farizrahman4u/loopgpt#setup-your-openai-api-key- for more details"
        )
    return key


class OpenAIModel(BaseModel):
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.8,
    ) -> str:
        import openai
        from openai.error import RateLimitError

        api_key = _getkey(self.api_key)
        num_retries = 3
        for _ in range(num_retries):
            try:
                if openai.api_type == "azure":
                    resp = openai.ChatCompletion.create(
                        engine=self.model,
                        messages=messages,
                        api_key=api_key,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )["choices"][0]["message"]["content"]
                else:
                    resp = openai.ChatCompletion.create(
                        model=self.model,
                        messages=messages,
                        api_key=api_key,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )["choices"][0]["message"]["content"]
                    return resp

            except RateLimitError:
                logger.warn("Rate limit exceeded. Retrying after 20 seconds.")
                time.sleep(20)
                continue

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        tokens_per_message, tokens_per_name = {
            "gpt-3.5-turbo": (4, -1),
            "gpt-35-turbo": (4, -1),
            "gpt-4": (3, 1),
            "gpt-4-32k": (3, 1),
        }[self.model]
        enc = tiktoken.encoding_for_model(self.model)
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(enc.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens

    def get_token_limit(self) -> int:
        return {
            "gpt-3.5-turbo": 4000,
            "gpt-35-turbo": 4000,
            "gpt-4": 8000,
            "gpt-4-32k": 32000,
        }[self.model]

    def config(self):
        cfg = super().config()
        cfg.update(
            {
                "model": self.model,
                "api_key": self.api_key,
            }
        )
        return cfg

    @classmethod
    def from_config(cls, config):
        return cls(config["model"], config.get("api_key", None))
