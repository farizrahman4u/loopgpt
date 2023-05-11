from loopgpt.embeddings import BaseEmbeddingProvider

import numpy as np

class DummyEmbeddingProvider(BaseEmbeddingProvider):
    def get(self, text):
        return np.zeros(768)
    
    def __call__(self, text):
        return self.get(text)
    
    def config(self):
        return {"class": self.__class__.__name__, "type": "embedding_provider"}
    
    @classmethod
    def from_config(cls, config):
        return cls()
