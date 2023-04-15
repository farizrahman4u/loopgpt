from loopgpt.constants import (
    DEFAULT_CONSTRAINTS,
    DEFAULT_RESPONSE_FORMAT,
    DEFAULT_EVALUATIONS,
)
from loopgpt.tools.browser import Browser
from loopgpt.tools.code import ExecutePythonFile
from loopgpt.tools.filesystem import FileSystemTools
from loopgpt.tools.shell import Shell
from loopgpt.tools.agent_manager import AgentManagerTools
from loopgpt.tools import deserialize as deserialize_tool
from loopgpt.models.openai_ import chat
from loopgpt.tools.google_search import GoogleSearch
from loopgpt.utils import token_counter
import json


class Agent:
    def __init__(self, name="LoopGPT", model="gpt-3.5-turbo"):
        self.name = name
        self.model = model
        self.sub_agents = {}
        self.tools = {}
        self.constraints = DEFAULT_CONSTRAINTS[:]
        self.evaluations = DEFAULT_EVALUATIONS[:]
        self.response_format = DEFAULT_RESPONSE_FORMAT
        self.history = []
        self._register_default_tools()

    def _default_tools(self):
        yield Shell()
        yield Browser()
        yield ExecutePythonFile()
        yield GoogleSearch()
        for tool_cls in FileSystemTools:
            yield tool_cls()
        for tool_cls in AgentManagerTools:
            yield tool_cls(self.sub_agents)

    def register_tool(self, tool):
        self.tools[tool.id] = tool

    def _register_default_tools(self):
        for tool in self._default_tools():
            self.register_tool(tool)

    def _get_full_prompt(self):
        prompt = {"role": "system", "content": self._get_seed_prompt()}
        return [prompt] + self.history

    def chat(self, message: str):
        self.history.append({"role": "user", "content": message})
        try:
            prompt = self._get_full_prompt()
            tokens_used = token_counter.count_message_tokens(prompt)
            while tokens_used > 4000:
                self.history.pop(0)
                prompt = self._get_full_prompt()
                tokens_used = token_counter.count_message_tokens(prompt)
            resp = chat(prompt, model=self.model)
        except Exception:
            self.history.pop()
            raise
        self.history.append({"role": "assistant", "content": resp})
        return resp

    def clear_history(self):
        self.history.clear()

    def clear_sub_agents(self):
        self.sub_agents.clear()

    def clear_state(self):
        self.clear_history()
        self.clear_sub_agents()

    def _get_seed_prompt(self):
        prompt = []
        prompt.append("Constraints:")
        for i, constraint in enumerate(self.constraints):
            prompt.append(f"{i + 1}. {constraint}")
        prompt.append("")
        prompt.append("Commands:")
        for i, tool in enumerate(self.tools.values()):
            prompt.append(f"{i + 1}. {tool.prompt()}")
        prompt.append("")
        prompt.append("Performance Evaluation:")
        for i, evaln in enumerate(self.evaluations):
            prompt.append(f"{i + 1}. {evaln}")
        prompt.append("")
        prompt.append(self.response_format)
        return "\n".join(prompt)

    def config(self, include_state=True):
        cfg = {
            "class": self.__class__.__name__,
            "name": self.name,
            "model": self.model,
            "tools": {k: v.serialize() for k, v in self.tools.items()},
            "constraints": list(self.constraints),
            "evaluations": list(self.evaluations),
            "response_format": self.response_format,
        }
        if include_state:
            cfg["sub_agents"] = {k: v.config() for k, v in self.sub_agents.items()}
            cfg["history"] = self.history[:]
        return cfg

    @classmethod
    def from_config(cls, config):
        agent = cls()
        agent.name = config["name"]
        agent.mdoel = config["model"]
        agent.tools = {k: deserialize_tool(v) for k, v in config["tools"].items()}
        agent.constraints = config["constraints"][:]
        agent.evaluations = config["evaluations"][:]
        agent.response_format = config["response_format"]
        agent.sub_agents = {
            k: cls.from_config(v) for k, v in config.get("sub_agents", {}).items()
        }
        agent.history = config.get("history", [])
        return agent

    def save(self, file, include_state=True):
        cfg = self.config(include_state=include_state)
        if hasattr(file, "write"):
            json.dump(cfg, file)
        elif isinstance(file, str):
            with open(file, "w") as f:
                json.dump(cfg, f)
        else:
            raise TypeError(f"Expected str or file like object. Received {type(f)}.")

    @classmethod
    def load(cls, file):
        if hasattr(file, "read"):
            cfg = json.load(file)
        elif isinstance(file, str):
            with open(file, "r") as f:
                cfg = json.load(f)
        else:
            raise TypeError(f"Expected str or file like object. Received {type(f)}.")
        return cls.from_config(cfg)
