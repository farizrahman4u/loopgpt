from typing import Optional
from loopgpt.embeddings.provider import BaseEmbeddingProvider
from loopgpt.utils.openai_key import get_openai_key
import numpy as np
import openai


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(
        self, model: str = "text-embedding-ada-002", api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key

    def get(self, text: str):
        api_key = get_openai_key(self.api_key)
        return np.array(
            openai.Embedding.create(
                input=[text], model="text-embedding-ada-002", api_key=api_key
            )["data"][0]["embedding"],
            dtype=np.float32,
        )

    def config(self):
        cfg = super().config()
        cfg.update({"model": self.model, "api_key": self.api_key})
        return cfg

    @classmethod
    def from_config(cls, config):
        return cls(config["model"], config.get("api_key"))
