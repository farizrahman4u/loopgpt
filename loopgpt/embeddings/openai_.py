from loopgpt.embeddings.provider import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model: str = "text-embedding-ada-002"):
        super(OpenAIEmbeddingProvider, self).__init__()
        self.model = model

    def get(self, text: str):
        import openai

        return openai.Embedding.create(input=[text], model="text-embedding-ada-002")[
            "data"
        ][0]["embedding"]

    def get_config(self):
        cfg = super().get_config()
        cfg.update({"model": self.model})
        return cfg

    @classmethod
    def from_config(cls, config):
        obj = cls()
        obj.model = config["model"]
        return obj
