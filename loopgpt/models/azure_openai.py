from typing import List, Dict, Optional
from loopgpt.models.openai_ import OpenAIModel
from loopgpt.utils.openai_key import get_openai_key
from loopgpt.logger import logger
from time import time

from openai.error import RateLimitError
import requests
import openai

def get_deployment_details(endpoint, deployment_id, api_version, api_key):
    api_key = get_openai_key(api_key)
    response = requests.get(
        f"{endpoint}/openai/deployments/{deployment_id}?api-version={api_version}", headers={"api-key": api_key}
    )
    return response.json()

def get_deployment_model(endpoint, deployment_id, api_version, api_key):
    details = get_deployment_details(endpoint, deployment_id, api_version, api_key)
    model = details["model"]

    return {
        "gpt-35-turbo": "gpt-3.5-turbo",
        "gpt-4": "gpt-4",
        "gpt-4-32k": "gpt-4-32k",
    }[model]


class AzureOpenAIModel(OpenAIModel):
    def __init__(self, deployment_id: str, api_key: Optional[str] = None):
        # sanity check
        assert openai.api_type == "azure", "AzureOpenAIModel can only be used with Azure API"

        self.deployment_id = deployment_id
        self.api_key = api_key
        self.endpoint = openai.api_base
        self.api_version = openai.api_version
        self.model = get_deployment_model(self.endpoint, self.deployment_id, self.api_version, self.api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.8,
    ) -> str:

        api_key = get_openai_key(self.api_key)
        num_retries = 3
        for _ in range(num_retries):
            try:
                resp = openai.ChatCompletion.create(
                    engine=self.deployment_id,
                    messages=messages,
                    api_key=api_key,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )["choices"][0]["message"]["content"]
                return resp

            except RateLimitError:
                logger.warn("Rate limit exceeded. Retrying after 20 seconds.")
                time.sleep(20)
                continue
    
    def config(self):
        cfg = super().config()
        cfg.update({
            "deployment_id": self.deployment_id,
        })
        return cfg
    
    @classmethod
    def from_config(cls, config):
        return cls(config["deployment_id"], config.get("api_key"))
