from loopgpt.embeddings.provider import BaseEmbeddingProvider
from sentence_transformers import SentenceTransformer


class RobertaLargeEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self):
        super(RobertaLargeEmbeddingProvider, self).__init__()
        self.model = SentenceTransformer('sentence-transformers/all-roberta-large-v1')

    def get(self, text: str):
        return self.model.encode(text)
