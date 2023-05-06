import numpy as np
import openai
from loopgpt.embeddings.openai_ import OpenAIEmbeddingProvider
from typing import Optional

from loopgpt.utils.openai_key import get_openai_key

class AzureOpenAIEmbeddingProvider(OpenAIEmbeddingProvider):
    def __init__(self, deployment_id: str, api_key: Optional[str] = None):
        self.deployment_id = deployment_id
        self.api_key = api_key
    
    def get(self, text: str):
        api_key = get_openai_key(self.api_key)
        return np.array(
            openai.Embedding.create(input=[text], engine=self.deployment_id, api_key=api_key)[
                "data"
            ][0]["embedding"],
            dtype=np.float32,
        )

    def config(self):
        cfg = {"deployment_id": self.deployment_id, "api_key": self.api_key}
        return cfg

    @classmethod
    def from_config(cls, config):
        return cls(config["deployment_id"], config["api_key"])