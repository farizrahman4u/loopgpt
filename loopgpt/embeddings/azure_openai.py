import numpy as np
from loopgpt.embeddings.openai_ import OpenAIEmbeddingProvider
from typing import Optional

from loopgpt.utils.openai_key import get_openai_key
from openai import AzureOpenAI


class AzureOpenAIEmbeddingProvider(OpenAIEmbeddingProvider):
    """Creates an Azure OpenAI embedding provider from a deployment ID. Can be created only when ``openai.api_type`` is set to ``azure``.

    :param deployment_id: The deployment ID of the embedding provider.
    :type deployment_id: str
    :param api_key: The API key to use for the embedding provider.
        If not specified, it will be found from ``openai.api_key`` or ``.env`` file or the ``OPENAI_API_KEY`` environment variable.
    :type api_key: str, optional

    .. note::
        See :class:`AzureOpenAIModel <loopgpt.models.azure_openai.AzureOpenAIModel>` also.
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
    ):
        self.model = model
        self.api_key = get_openai_key(api_key)
        self.api_version = api_version
        self.azure_endpoint = azure_endpoint
        self.client = AzureOpenAI(
            api_key=self.api_key, api_version=api_version, azure_endpoint=azure_endpoint
        )

    def get(self, text: str):
        return np.array(
            self.client.embeddings.create(input=[text], model=self.model)
            .data[0]
            .embedding,
            dtype=np.float32,
        )

    def config(self):
        cfg = super().config()
        cfg.update(
            {
                "model": self.model,
                "api_key": self.api_key,
                "api_version": self.api_version,
                "azure_endpoint": self.azure_endpoint,
            }
        )
        return cfg

    @classmethod
    def from_config(cls, config):
        return cls(
            config["model"],
            config["api_key"],
            config["api_version"],
            config["azure_endpoint"],
        )
