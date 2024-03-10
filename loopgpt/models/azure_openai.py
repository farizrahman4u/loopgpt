from typing import List, Dict, Optional
from loopgpt.models.openai_ import OpenAIModel
from loopgpt.utils.openai_key import get_openai_key
from loopgpt.logger import logger
import time

from openai import RateLimitError
from openai import AzureOpenAI
import requests


def get_deployment_details(endpoint, model_id, api_version, api_key):
    api_key = get_openai_key(api_key)
    response = requests.get(
        f"{endpoint}/openai/deployments/{model_id}?api-version={api_version}",
        headers={"api-key": api_key},
    )
    return response.json()


def get_deployment_model(endpoint, model_id, api_version, api_key):
    details = get_deployment_details(endpoint,  model_id, api_version, api_key)
    model = details["model"]

    return {
        "gpt-35-turbo": "gpt-3.5-turbo",
        "gpt-4": "gpt-4",
        "gpt-4-32k": "gpt-4-32k",
    }[model]


class AzureOpenAIModel(OpenAIModel):
    """Creates an Azure OpenAI model from a deployment ID. Can be created only when ``openai.api_type`` is set to ``azure``.

    :param deployment_id: The deployment ID of the model.
    :type deployment_id: str
    :param api_key: The API key to use for the model.
        If not specified, it will be found from ``openai.api_key`` or ``.env`` file or the ``OPENAI_API_KEY`` environment variable.
    :type api_key: str, optional
    :raises AssertionError: If ``openai.api_type`` is not set to ``azure``.

    .. note::
        You will also need an embedding provider deployed (e.g., text-embedding-ada-002) for creating an agent.

    Example:

    .. code-block:: python

        import os
        import openai
        import loopgpt
        from loopgpt.models import AzureOpenAIModel
        from loopgpt.embeddings import AzureOpenAIEmbeddingProvider

        openai.api_type = "azure"
        openai.api_base = "https://<your deployment>.openai.azure.com/"
        openai.api_version = "2023-03-15-preview"
        openai.api_key = os.getenv("OPENAI_API_KEY")

        model = AzureOpenAIModel("my-gpt4-deployment")
        embedding_provider = AzureOpenAIEmbeddingProvider("my-embeddings-deployment")

        agent = loopgpt.Agent(model=model, embedding_provider=embedding_provider)
        agent.chat("Hello, how are you?")
    """

    def __init__(self, model: str, api_key: Optional[str] = None, api_version: Optional[str] = None, azure_endpoint: Optional[str] = None):
        # sanity check
        self.model_id = model
        self.api_key = get_openai_key(api_key)
        self.api_version = api_version
        self.azure_endpoint = azure_endpoint

        self.model = get_deployment_model(
            azure_endpoint, self.model_id, api_version, api_key
        )

        self.client = AzureOpenAI(api_key=self.api_key, api_version=api_version, azure_endpoint=azure_endpoint)

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.8,
    ) -> str:
        num_retries = 3
        for _ in range(num_retries):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                ).choices[0].message.content
                return resp

            except RateLimitError:
                logger.warn("Rate limit exceeded. Retrying after 20 seconds.")
                time.sleep(20)
                continue

    def config(self):
        cfg = super().config()
        cfg.update(
            {
                "model": self.model_id,
                "api_key": self.api_key,
                "api_version": self.api_version,
                "azure_endpoint": self.azure_endpoint,
            }
        )
        return cfg

    @classmethod
    def from_config(cls, config):
        return cls(config["model"], config.get("api_key"), config.get("api_version"), config.get("azure_endpoint"))
