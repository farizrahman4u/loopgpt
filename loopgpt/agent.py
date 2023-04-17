from loopgpt.constants import (
    DEFAULT_CONSTRAINTS,
    DEFAULT_RESPONSE_FORMAT,
    DEFAULT_EVALUATIONS,
    DEFAULT_RESOURCES,
    SEED_INPUT,
    DEFAULT_AGENT_NAME,
    DEFAULT_AGENT_DESCRIPTION,
)
from loopgpt.memory import from_config as memory_from_config
from loopgpt.models.openai_ import chat, count_tokens, get_token_limit
from loopgpt.tools import builtin_tools, from_config as tool_from_config
from loopgpt.memory.local_memory import LocalMemory
from loopgpt.embeddings.openai_ import OpenAIEmbeddingProvider
from loopgpt.loops.cli import cli
from loopgpt.utils.spinner import spinner


from typing import *

import json
import time
import ast


class Agent:
    def __init__(
        self,
        name=DEFAULT_AGENT_NAME,
        description=DEFAULT_AGENT_DESCRIPTION,
        goals=None,
        model="gpt-3.5-turbo",
        temperature=0.8,
    ):
        self.name = name
        self.description = description
        self.goals = goals or []
        self.model = model
        self.temperature = temperature
        self.sub_agents = {}
        self.memory = LocalMemory(embedding_provider=OpenAIEmbeddingProvider())
        self.constraints = DEFAULT_CONSTRAINTS[:]
        self.evaluations = DEFAULT_EVALUATIONS[:]
        self.resources = DEFAULT_RESOURCES[:]
        self.response_format = DEFAULT_RESPONSE_FORMAT
        self.history = []
        tools = [tool_type() for tool_type in builtin_tools()]
        self.tools = {tool.id: tool for tool in tools}
        self.staging_tool = None
        self.tool_response = None

    def get_full_prompt(self, user_input: str = ""):
        header = {"role": "system", "content": self.header_prompt()}
        dtime = {
            "role": "system",
            "content": f"The current time and date is {time.strftime('%c')}",
        }
        prompt = [header, dtime]
        relevant_memory = self.memory.get(str(self.history[-10:]), 10)
        if relevant_memory:
            # Add as many documents from memory as possible while staying under the token limit
            token_limit = 2500
            while relevant_memory:
                memstr = "\n".join(relevant_memory)
                context = {
                    "role": "system",
                    "content": f"This reminds you of these events from your past:\n{memstr}\n",
                }
                token_count = count_tokens(prompt + [context], model=self.model)
                if token_count < token_limit:
                    break
                relevant_memory = relevant_memory[:-1]
            prompt.append(context)
        history = self.history
        user_prompt = [{"role": "user", "content": user_input}] if user_input else []
        prompt = prompt[:2] + history + prompt[2:] + user_prompt
        for p in prompt:
            assert isinstance(p, dict), p
        token_limit = get_token_limit(self.model) - 1000  # 1000 reserved for response
        token_count = count_tokens(prompt, model=self.model)
        while (
            history[1:] and token_count > token_limit
        ):  # keep at least 1 message from history
            history = history[1:]
            prompt.pop(2)
            token_count = count_tokens(prompt, model=self.model)
        return prompt, token_count

    @spinner
    def chat(self, message: str = SEED_INPUT, run_tool=False) -> Union[str, Dict]:
        if self.staging_tool:
            if run_tool:
                if self.staging_tool.get("name") == "task_complete":
                    self.history.append(
                        {"role": "system", "content": "Completed all user specified tasks."}
                    )
                    message = ""
                output = self.run_staging_tool()
                self.tool_response = output
                self.memory.add(
                    f"Assistant reply: {self.staging_response}\nResult: {output}\nHuman Feedback: {message}"
                )
            else:
                self.history.append(
                    {
                        "role": "system",
                        "content": f"User did not approve running {self.staging_tool}.",
                    }
                )
                self.memory.add(
                    f"Assistant reply: {self.staging_response}\nResult: (User did not approve)\nHuman Feedback: {message}"
                )
            self.staging_tool = None
            self.staging_response = None
        full_prompt, token_count = self.get_full_prompt(message)
        token_limit = get_token_limit(self.model)
        resp = chat(
            full_prompt,
            model=self.model,
            max_tokens=token_limit - token_count,
            temperature=self.temperature,
        )
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": resp})
        try:
            resp = self._load_json(resp)
            if "name" in resp:
                resp = {"command": resp}
            self.staging_tool = resp["command"]
            self.staging_response = resp
        except Exception as e:
            pass
        return resp

    def _load_json(self, s):
        if s.startswith("Assistant Reply {"):
            s = s[len("Assistant Reply ") :]
        if "Result: {" in s:
            s = s.split("Result: {}", 1)[0] 
        if "{" not in s or "}" not in s:
            raise Exception()
        try:
            return json.loads(s)
        except Exception:
            s = s[s.find("{") : s.rfind("}") + 1]
            try:
                return json.loads(s)
            except Exception:
                try:
                    s = s.replace("\n", " ")
                    return ast.literal_eval(s)
                except Exception:
                    s = s + "}"
                    try:
                        return ast.literal_eval(s)
                    except:
                        raise

    def last_user_input(self) -> str:
        for msg in self.history[::-1]:
            if msg["role"] == "user":
                return msg["content"]
        return ""

    def last_agent_response(self) -> str:
        for msg in self.history[::-1]:
            if msg["role"] == "assistant":
                return msg["content"]
        return ""

    def run_staging_tool(self):
        if "name" not in self.staging_tool:
            self.history.append(
                {
                    "role": "system",
                    "content": f"Command name not provided. Make sure to follow the specified response format.",
                }
            )
            return
        tool_id = self.staging_tool["name"]
        if tool_id == "task_complete":
            resp = {"success": True}
        elif tool_id == "do_nothing":
            resp = {"response": "Nothing Done."}
        else:
            if "args" not in self.staging_tool:
                self.history.append(
                    {
                        "role": "system",
                        "content": f"Command args not provided. Make sure to follow the specified response format.",
                    }
                )
                return
            kwargs = self.staging_tool["args"]
            found = False
            for k, tool in self.tools.items():
                if k == tool_id:
                    found = True
                    break
            if not found:
                self.history.append(
                    {"role": "system", "content": f"Command {tool_id} does not exist."}
                )
                return
            resp = tool.run(**kwargs)
        self.history.append(
            {
                "role": "system",
                "content": f"Response from {tool_id}:\n{json.dumps(resp)}",
            }
        )
        return resp

    def clear_state(self):
        self.staging_tool = None
        self.staging_response = None
        self.tool_response = None
        self.history.clear()
        self.sub_agents.clear()
        self.memory.clear()

    def header_prompt(self):
        prompt = []
        prompt.append(self.persona_prompt())
        if self.goals:
            prompt.append(self.goals_prompt())
        if self.constraints:
            prompt.append(self.constraints_prompt())
        if self.tools:
            prompt.append(self.tools_prompt())
        if self.resources:
            prompt.append(self.resources_prompt())
        if self.evaluations:
            prompt.append(self.evaluation_prompt())
        prompt.append(self.response_format)
        return "\n".join(prompt) + "\n"

    def persona_prompt(self):
        return (
            f"You are {self.name}, {self.description}."
            "Your decisions must always be made independently without"
            "seeking user assistance. Play to your strengths as an LLM and pursue"
            " simple strategies with no legal complications.\n"
        )

    def goals_prompt(self):
        prompt = []
        prompt.append(f"GOALS:")
        for i, g in enumerate(self.goals):
            prompt.append(f"{i + 1}. {g}")
        return "\n".join(prompt) + "\n"

    def constraints_prompt(self):
        prompt = []
        prompt.append("Constraints:")
        for i, constraint in enumerate(self.constraints):
            prompt.append(f"{i + 1}. {constraint}")
        return "\n".join(prompt) + "\n"

    def tools_prompt(self):
        prompt = []
        prompt.append("Commands:")
        for i, tool in enumerate(self.tools.values()):
            tool.agent = self
            prompt.append(f"{i + 1}. {tool.prompt()}")
        task_complete_command = {
            "name": "task_complete",
            "description": "Execute this command when all given tasks are completed.",
            "args": {},
            "response_format": {"success": "true"},
        }
        do_nothing_command = {
            "name": "do_nothing",
            "description": "Do nothing. Use this command only when there is no action to be performed.",
            "args": {},
            "response_format": {"response": "Nothing Done."},
        }
        prompt.append(f"{i + 2}. {json.dumps(task_complete_command)}")
        prompt.append(f"{i + 3}. {json.dumps(do_nothing_command)}")
        return "\n".join(prompt) + "\n"

    def resources_prompt(self):
        prompt = []
        prompt.append("Resources:")
        for i, res in enumerate(self.resources):
            prompt.append(f"{i + 1}. {res}")
        return "\n".join(prompt) + "\n"

    def evaluation_prompt(self):
        prompt = []
        prompt.append("Performance Evaluation:")
        for i, evaln in enumerate(self.evaluations):
            prompt.append(f"{i + 1}. {evaln}")
        return "\n".join(prompt) + "\n"

    def config(self, include_state=True):
        cfg = {
            "class": self.__class__.__name__,
            "type": "agent",
            "name": self.name,
            "description": self.description,
            "goals": self.goals[:],
            "model": self.model,
            "temperature": self.temperature,
            "tools": [tool.config() for tool in self.tools.values()],
            "constraints": list(self.constraints),
            "evaluations": list(self.evaluations),
        }
        if include_state:
            cfg.update(
                {
                    "sub_agents": {k: v.config() for k, v in self.sub_agents.items()},
                    "history": self.history[:],
                    "memory": self.memory.config(),
                    "staging_tool": self.staging_tool,
                    "staging_response": self.staging_response,
                    "tool_response": self.tool_response,
                }
            )
        return cfg

    @classmethod
    def from_config(cls, config):
        agent = cls()
        agent.name = config["name"]
        agent.description = config["description"]
        agent.goals = config["goals"][:]
        agent.temperature = config["temperature"]
        agent.model = config["model"]
        agent.tools = {tool.id: tool for tool in map(tool_from_config, config["tools"])}
        agent.constraints = config["constraints"][:]
        agent.evaluations = config["evaluations"][:]
        agent.sub_agents = {
            k: cls.from_config(v) for k, v in config.get("sub_agents", {}).items()
        }
        agent.history = config.get("history", [])
        memory = config.get("memory")
        if memory:
            agent.memory = memory_from_config(memory)
        agent.staging_tool = config.get("staging_tool")
        agent.staging_response = config.get("staging_response")
        agent.tool_response = config.get("tool_response")
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

    def cli(self):
        cli(self)
