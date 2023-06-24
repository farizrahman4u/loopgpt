from typing import *
import loopgpt.agent
import inspect
import re


def camel_case_split(str):
    return re.findall(r"[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", str)


class BaseTool:
    def __init__(self, *args, **kwargs):
        self._agent = None

    @property
    def agent(self):
        return loopgpt.agent.ACTIVE_AGENT or self._agent

    @agent.setter
    def agent(self, agent):
        self._agent = agent

    @property
    def id(self) -> str:
        return "_".join(camel_case_split(self.__class__.__name__)).lower()

    def run(**kwargs) -> str:
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
