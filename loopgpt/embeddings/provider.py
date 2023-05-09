import numpy as np


class BaseEmbeddingProvider:
    """Base class for all embedding providers."""

    def get(self, text: str) -> np.ndarray:
        raise NotImplementedError()

    def __call__(self, text: str):
        return self.get(text)

    def config(self):
        return {
            "class": self.__class__.__name__,
            "type": "embedding_provider",
        }

    @classmethod
    def from_config(cls, config):
        return cls()
