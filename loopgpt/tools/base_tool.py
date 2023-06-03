from typing import *
import inspect
import re


def camel_case_split(str):
    return re.findall(r"[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", str)


class BaseTool:
    @property
    def id(self) -> str:
        return "_".join(camel_case_split(self.__class__.__name__)).lower()

    def run(**kwrags) -> str:
        raise NotImplementedError()

    def prompt(self):
        sig = inspect.signature(self.run)
        return f'def {self.id}{sig}:\n\t"""{self.__doc__}\n\t"""'.expandtabs(4)

    def config(self):
        return {
            "class": self.__class__.__name__,
            "type": "tool",
        }

    @classmethod
    def from_config(cls, config):
        return cls()
