from typing import Dict, List, Optional, Tuple, Any, Generic, TypeVar


class BaseModel:
    """Base class for all models."""

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.8,
    ) -> str:
        raise NotImplementedError()

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        raise NotImplementedError()

    def get_token_limit(self):
        raise NotImplementedError()

    def config(self):
        return {"class": self.__class__.__name__, "type": "model"}

    @classmethod
    def from_config(cls, config):
        raise cls()
