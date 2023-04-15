from typing import *
import json
import re
import pickle
import base64


def camel_case_split(str):
    return re.findall(r"[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", str)


class BaseTool:
    @property
    def id(self) -> str:
        return "_".join(camel_case_split(self.__class__.__name__)).lower()

    @property
    def desc(self) -> str:
        return " ".join(camel_case_split(self.__class__.__name__))

    @property
    def args(self) -> Dict[str, str]:
        raise NotImplementedError()

    def run(**kwrags) -> str:
        raise NotImplementedError()

    @property
    def resp(self) -> Dict[str, str]:
        raise NotImplementedError()

    def prompt(self):
        return f"{self.id}: " + json.dumps(
            {"description": self.desc, "args": self.args, "response_format": self.resp}
        )

    def config(self):
        return {
            "class": self.__class__.__name__,
        }

    @classmethod
    def from_config(cls, config):
        config = config.copy()
        config.pop("class", None)
        return cls(**config)

    def serialize(self):
        from loopgpt.tools import is_builtin_tool, is_serde_overridden
        if is_builtin_tool or is_serde_overridden:
            return self.config()
        return {"class": self.__class__.__name__, "pickle": base64.b64encode(pickle.dumps(self)).decode("ascii")}
