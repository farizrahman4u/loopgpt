from loopgpt.tools.agent_manager import (
    CreateAgent,
    MessageAgent,
    DeleteAgent,
    ListAgents,
)
from loopgpt.tools.base_tool import BaseTool
from loopgpt.tools.browser import Browser
from loopgpt.tools.code import ExecutePythonFile
from loopgpt.tools.google_search import GoogleSearch
from loopgpt.tools.filesystem import (
    ReadFile,
    WriteFile,
    AppendFile,
    DeleteFile,
    CheckIfFileExists,
    FileSystemTools,
)
from loopgpt.tools.shell import Shell
import pickle
import base64


builtin_tools = [
    c for c in globals().values() if isinstance(c, type) and issubclass(c, BaseTool)
]
builtin_tools_names = [c.__name__ for c in builtin_tools]


def from_config(config) -> BaseTool:
    class_name = config["class"]
    clss = globals()[class_name]
    return clss.from_config(config)


def is_builtin_tool(tool) -> bool:
    if isinstance(tool, str):
        return tool in builtin_tools_names
    elif isinstance(tool, type):
        return tool in builtin_tools
    elif isinstance(tool, BaseTool):
        return tool.__class__ in builtin_tools
    else:
        raise TypeError(f"{tool} is not a valid a tool or tool type.")


def is_serde_overridden(tool):
    if isinstance(tool, BaseTool):
        tool = tool.__class__
    if not isinstance(tool, type):
        raise TypeError(f"{tool} is not a type.")
    if not issubclass(tool, BaseTool):
        raise TypeError(f"Class {tool} does not inherit from BaseTool.")
    return not (
        tool.from_config == BaseTool.from_config and tool.config == BaseTool.config
    )


def deserialize(config) -> BaseTool:
    if len(config) == 2 and "pickle" in config:
        return pickle.loads(base64.decode(config["pickle"].encode("ascii")))
    return from_config(config)
