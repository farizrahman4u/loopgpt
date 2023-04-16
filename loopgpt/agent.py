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
from loopgpt.tools.memory_manager import MemoryManagerTools
from loopgpt.tools import from_config as tool_from_config
from loopgpt.memory import from_config as memory_from_config
from loopgpt.models.openai_ import chat
from loopgpt.tools.google_search import GoogleSearch
from loopgpt.tools import builtin_tools
from loopgpt.memory.local_memory import LocalMemory
from loopgpt.embeddings.openai_ import OpenAIEmbeddingProvider

import json


class Agent:
    def __init__(self, name="LoopGPT", model="gpt-3.5-turbo"):
        self.name = name
        self.model = model
        self.sub_agents = {}
        self.memory = LocalMemory(embedding_provider=OpenAIEmbeddingProvider())
        self.constraints = DEFAULT_CONSTRAINTS[:]
        self.evaluations = DEFAULT_EVALUATIONS[:]
        self.response_format = DEFAULT_RESPONSE_FORMAT
        self.history = []
        self.tools = [tool_type() for tool_type in builtin_tools()]

    def _get_full_prompt(self):
        prompt = {"role": "system", "content": self._get_seed_prompt()}
        return [prompt] + self.history

    def chat(self, message: str):
        self.history.append({"role": "user", "content": message})
        try:
            resp = chat(self._get_full_prompt(), model=self.model)
        except Exception:
            self.history.pop()
            raise
        self.history.append({"role": "assistant", "content": resp})
        return resp

    def clear_state(self):
        self.history.clear()
        self.sub_agents.clear()
        self.memory.clear()

    def _get_seed_prompt(self):
        prompt = []
        prompt.append("Constraints:")
        for i, constraint in enumerate(self.constraints):
            prompt.append(f"{i + 1}. {constraint}")
        prompt.append("")
        prompt.append("Commands:")
        for i, tool in enumerate(self.tools):
            tool.agent = self
            prompt.append(f"{i + 1}. {tool.prompt()}")
        prompt.append("")
        prompt.append("Resources:")
        prompt.append("1. Internet access for searches and information gathering.")
        prompt.append("2. Long Term memory management.")
        prompt.append("3. GPT-3.5 powered Agents for delegation of simple tasks.")
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
            "type": "agent",
            "name": self.name,
            "model": self.model,
            "tools": [tool.config() for tool in self.tools],
            "constraints": list(self.constraints),
            "evaluations": list(self.evaluations),
            "response_format": self.response_format,
        }
        if include_state:
            cfg.update(
                {
                    "sub_agents": {k: v.config() for k, v in self.sub_agents.items()},
                    "history": self.history[:],
                    "memory": self.memory.config(),
                }
            )
        return cfg

    @classmethod
    def from_config(cls, config):
        agent = cls()
        agent.name = config["name"]
        agent.mdoel = config["model"]
        agent.tools = list(map(tool_from_config, config["tools"]))
        agent.constraints = config["constraints"][:]
        agent.evaluations = config["evaluations"][:]
        agent.response_format = config["response_format"]
        agent.sub_agents = {
            k: cls.from_config(v) for k, v in config.get("sub_agents", {}).items()
        }
        agent.history = config.get("history", [])
        memory = config.get("memory")
        if memory:
            agent.memory = memory_from_config(memory)
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
