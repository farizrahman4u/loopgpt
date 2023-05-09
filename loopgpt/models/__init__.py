from loopgpt.models.stable_lm import StableLMModel
from loopgpt.models.llama_cpp import LlamaCppModel
from loopgpt.models.openai_ import OpenAIModel
from loopgpt.models.azure_openai import AzureOpenAIModel
from loopgpt.models.hf import HuggingFaceModel
from loopgpt.models.base import *


user_providers = {}


def register_model_type(provider):
    if isinstance(provider, BaseModel):
        provider = provider.__class__
    if not isinstance(provider, type):
        raise TypeError(f"{provider} is not a class")
    if not issubclass(provider, BaseModel):
        raise TypeError(f"{provider} does not inherit from ConversationalModelBase")
    user_providers[provider.__name__] = provider


def from_config(config) -> BaseModel:
    class_name = config["class"]
    clss = user_providers.get(class_name) or globals()[class_name]
    return clss.from_config(config)
