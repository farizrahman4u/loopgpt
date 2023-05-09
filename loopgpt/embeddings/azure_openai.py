import numpy as np
import openai
from loopgpt.embeddings.openai_ import OpenAIEmbeddingProvider
from typing import Optional

from loopgpt.utils.openai_key import get_openai_key


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

    def __init__(self, deployment_id: str, api_key: Optional[str] = None):
        # sanity check
        assert (
            openai.api_type == "azure"
        ), "AzureOpenAIModel can only be used with Azure API"

        self.deployment_id = deployment_id
        self.api_key = api_key

    def get(self, text: str):
        api_key = get_openai_key(self.api_key)
        return np.array(
            openai.Embedding.create(
                input=[text], engine=self.deployment_id, api_key=api_key
            )["data"][0]["embedding"],
            dtype=np.float32,
        )

    def config(self):
        cfg = {"deployment_id": self.deployment_id, "api_key": self.api_key}
        return cfg

    @classmethod
    def from_config(cls, config):
        return cls(config["deployment_id"], config["api_key"])
