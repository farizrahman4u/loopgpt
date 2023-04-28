from loopgpt.embeddings.provider import BaseEmbeddingProvider


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model_id: str = "sentence-transformers/all-roberta-large-v1"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "Please install sentence-transformers (pip install sentence-transformers) to use this embedding provider."
            ) from e
        super(HuggingFaceEmbeddingProvider, self).__init__()
        self.model_id = model_id
        self.model = SentenceTransformer(model_id)

    def config(self):
        config = super(HuggingFaceEmbeddingProvider, self).config()
        config.update({"model_id": self.model_id})
        return config

    @classmethod
    def from_config(cls, config):
        return cls(model_id=config["model_id"])

    def get(self, text: str):
        return self.model.encode(text)
