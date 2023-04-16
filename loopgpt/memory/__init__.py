from loopgpt.memory.base_memory import BaseMemory
from loopgpt.memory.local_memory import LocalMemory


user_providers = {}


def register_memory_type(provider):
    if isinstance(provider, BaseMemory):
        provider = provider.__class__
    if not isinstance(provider, type):
        raise TypeError(f"{provider} is not a class")
    if not issubclass(provider, BaseMemory):
        raise TypeError(f"{provider} does not inherit from BaseMemory")
    user_providers[provider.__name__] = provider


def from_config(config) -> BaseMemory:
    class_name = config["class"]
    clss = user_providers.get(class_name) or globals()[class_name]
    return clss.from_config(config)
