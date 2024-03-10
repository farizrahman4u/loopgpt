from typing import Optional
from loopgpt.embeddings.base import BaseEmbeddingProvider
from loopgpt.utils.openai_key import get_openai_key
from openai import OpenAI
import numpy as np


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(
        self, model: str = "text-embedding-ada-002", api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = get_openai_key(api_key)
        self.client = OpenAI(api_key=self.api_key)

    def get(self, text: str):
        return np.array(
            self.client.embeddings.create(
                input=[text],
                model=self.model,
            )
            .data[0]
            .embedding,
            dtype=np.float32,
        )

    def config(self):
        cfg = super().config()
        cfg.update({"model": self.model, "api_key": self.api_key})
        return cfg

    @classmethod
    def from_config(cls, config):
        return cls(config["model"], config.get("api_key"))
