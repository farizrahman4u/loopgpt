from typing import *


class BaseMemory:
    def add(doc: str):
        raise NotImplementedError()

    def get(query: str, k: int) -> List[str]:
        raise NotImplementedError()

    def get_config(self):
        return {"class": self.__class__.__name__}

    @classmethod
    def from_config(cls, config):
        raise cls()
