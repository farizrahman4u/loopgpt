from loopgpt.memory.base_memory import BaseMemory
from loopgpt.embeddings import from_config as embedding_provider_from_config
from deeplake.core.vectorstore import VectorStore
from typing import Callable, Optional


class DeepLakeMemory(BaseMemory):
    def __init__(self, path: str, embedding_provider: Callable, **kwargs):
        super(BaseMemory, self).__init__()
        self.embedding_provider = embedding_provider
        self.vectorstore = VectorStore(
            path, embedding_function=self._embedding_function, **kwargs
        )

    def __len__(self):
        return len(self.vectorstore)

    def _embedding_function(self, x):
        return [self.embedding_provider(y) for y in x]

    def add(self, doc: str, key: Optional[str] = None):
        if not key:
            key = doc
        self.vectorstore.add(text=[doc], embedding_data=[key], metadata=[{}])

    def get(self, query: str, k: int):
        try:
            return self.vectorstore.search(
                [query], embedding_function=self._embedding_function, k=k
            )["text"]
        except ValueError:
            return []

    def config(self):
        cfg = super().config()
        cfg.update(
            {
                "path": self.vectorstore.dataset.path,
                "embedding_provider": self.embedding_provider.config(),
            }
        )
        return cfg

    @classmethod
    def from_config(cls, config):
        provider = embedding_provider_from_config(config["embedding_provider"])
        path = config["path"]
        obj = cls(path, provider)
        return obj

    def clear(self):
        # self.vectorstore.delete(delete_all=True)
        print("DELETING MEMORY")
        pass
