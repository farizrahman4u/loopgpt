from loopgpt.constants import (
    DEFAULT_RESPONSE_FORMAT_,
    INIT_PROMPT,
    DEFAULT_AGENT_NAME,
    DEFAULT_AGENT_DESCRIPTION,
    NEXT_PROMPT,
    NEXT_PROMPT_SMALL,
    AgentStates,
)
from loopgpt.memory import from_config as memory_from_config
from loopgpt.models import (
    OpenAIModel,
    AzureOpenAIModel,
    from_config as model_from_config,
)
from loopgpt.tools import builtin_tools, from_config as tool_from_config
from loopgpt.tools.code import ai_function
from loopgpt.memory.local_memory import LocalMemory
from loopgpt.embeddings import OpenAIEmbeddingProvider, AzureOpenAIEmbeddingProvider
from loopgpt.utils.spinner import spinner
from loopgpt.loops import cli


from typing import *

import openai
import json
import time
import ast


class Agent:
    """Creates a new LoopGPT agent.

    :param name: The name of the agent. Defaults to AGENT_NAME.
    :type name: str, optional
    :param description: A description of the agent. Defaults to DEFAULT_AGENT_DESCRIPTION.
    :type description: str, optional
    :param goals: A list of goals for the agent. Defaults to None.
    :type goals: list, optional
    :param model: The model to use for the agent.
        Strings are accepted only for OpenAI models. Specify a :class:`~loopgpt.models.base.BaseModel` object for other models.
        Defaults to "gpt-3.5-turbo".
    :type model: str, :class:`~loopgpt.models.base.BaseModel`, optional
    :param embedding_provider: The embedding provider to use for the agent.
        Defaults to :class:`~loopgpt.embeddings.OpenAIEmbeddingProvider`.
        Specify a :class:`~loopgpt.embeddings.provider.BaseEmbeddingProvider` object to use other embedding providers.
    :type embedding_provider: :class:`~loopgpt.embeddings.provider.BaseEmbeddingProvider`, optional
    :param temperature: The temperature to use for agent's chat completion. Defaults to 0.8.
    :type temperature: float, optional
    """

    def __init__(
        self,
        name=DEFAULT_AGENT_NAME,
        description=DEFAULT_AGENT_DESCRIPTION,
        goals=None,
        model=None,
        embedding_provider=None,
        temperature=0.8,
    ):
        if openai.api_type == "azure":
            if model is None:
                raise ValueError(
                    "You must provide an AzureOpenAIModel to the `model` argument when using the OpenAI Azure API"
                )
            if embedding_provider is None:
                raise ValueError(
                    "You must provide a deployed embedding provider to the `embedding_provider` argument when using the OpenAI Azure API"
                )

        if model is None:
            model = OpenAIModel("gpt-3.5-turbo")
        elif isinstance(model, str):
            model = OpenAIModel(model)

        if embedding_provider is None:
            embedding_provider = OpenAIEmbeddingProvider()

        self.name = name
        self.description = description
        self.goals = goals or []
        self.model = model
        self.embedding_provider = embedding_provider
        self.temperature = temperature
        self.sub_agents = {}
        self.memory = LocalMemory(embedding_provider=embedding_provider)
        self.history = []
        tools = [tool_type() for tool_type in builtin_tools()]
        self.tools = {tool.id: tool for tool in tools}
        self.staging_tool = None
        self.staging_response = None
        self.tool_response = None
        self.init_prompt = INIT_PROMPT
        self.next_prompt = NEXT_PROMPT
        self.progress = []
        self.plan = []
        self.constraints = []
        self.state = AgentStates.START

    def _get_non_user_messages(self, n):
        msgs = [
            msg
            for msg in self.history
            if msg["role"] != "user"
            and not (msg["role"] == "system" and "do_nothing" in msg["content"])
        ]
        return msgs[-n - 1 : -1]

    def get_full_prompt(self, user_input: str = ""):
        header = {"role": "system", "content": self.header_prompt()}
        dtime = {
            "role": "system",
            "content": f"The current time and date is {time.strftime('%c')}",
        }
        msgs = self._get_non_user_messages(10)
        relevant_memory = self.memory.get(str(msgs), 5)
        user_prompt = [{"role": "user", "content": user_input}] if user_input else []
        history = self._get_compressed_history()

        def _msgs():
            msgs = [header, dtime]
            msgs += history[:-1]
            if relevant_memory:
                memstr = "\n".join(relevant_memory)
                context = {
                    "role": "system",
                    "content": f"You have the following items in your memory as a result of previously executed commands:\n{memstr}\n",
                }
                msgs.append(context)
            msgs += history[-1:]
            msgs += user_prompt
            return msgs

        maxtokens = self.model.get_token_limit() - 1000
        while True:
            msgs = _msgs()
            ntokens = self.model.count_tokens(msgs)
            if ntokens < maxtokens:
                break
            else:
                if len(history) > 1:
                    history = history[1:]
                elif relevant_memory:
                    relevant_memory = relevant_memory[1:]
                else:
                    break
        return msgs, ntokens

    def _get_compressed_history(self):
        hist = self.history[:]
        system_msgs = [i for i in range(len(hist)) if hist[i]["role"] == "system"]
        assist_msgs = [i for i in range(len(hist)) if hist[i]["role"] == "assistant"]
        for i in assist_msgs:
            entry = hist[i].copy()
            try:
                respd = json.loads(entry["content"])
                thoughts = respd.get("thoughts")
                if thoughts:
                    thoughts.pop("reasoning", None)
                    thoughts.pop("speak", None)
                    thoughts.pop("text", None)
                    thoughts.pop("plan", None)
                entry["content"] = json.dumps(respd, indent=2)
                hist[i] = entry
            except:
                pass
        user_msgs = [i for i in range(len(hist)) if hist[i]["role"] == "user"]
        hist = [hist[i] for i in range(len(hist)) if i not in user_msgs]
        return hist

    def get_full_message(self, message: Optional[str]):
        if self.state == AgentStates.START:
            return self.init_prompt + "\n\n" + (message or "")
        else:
            return self.next_prompt + "\n\n" + (message or "")

    @spinner
    def chat(
        self, message: Optional[str] = None, run_tool=False
    ) -> Optional[Union[str, Dict]]:
        if self.state == AgentStates.STOP:
            raise ValueError(
                "This agent has completed its tasks. It will not accept any more messages."
                " You can do `agent.clear_state()` to start over with the same goals."
            )
        message = self.get_full_message(message)
        if self.staging_tool:
            tool = self.staging_tool
            if run_tool:
                output = self.run_staging_tool()
                self.tool_response = output
                if tool.get("name") == "task_complete":
                    self.history.append(
                        {
                            "role": "system",
                            "content": "Completed all user specified tasks.",
                        }
                    )
                    self.state = AgentStates.STOP
                    return
                if tool.get("name") != "do_nothing":
                    pass
                    # TODO We dont have enough space for this in gpt3
                    # self.memory.add(
                    #     f"Command \"{tool['name']}\" with args {tool['args']} returned :\n {output}"
                    # )
            else:
                self.history.append(
                    {
                        "role": "system",
                        "content": f"User did not approve running {tool.get('name', tool)}.",
                    }
                )
                # self.memory.add(
                #     f"User disapproved running command \"{tool['name']}\" with args {tool['args']} with following feedback\n: {message}"
                # )
            self.staging_tool = None
            self.staging_response = None
        full_prompt, token_count = self.get_full_prompt(message)
        token_limit = self.model.get_token_limit()
        max_tokens = min(1000, max(token_limit - token_count, 0))
        assert max_tokens
        resp = self.model.chat(
            full_prompt,
            max_tokens=max_tokens,
            temperature=self.temperature,
        )
        try:
            resp = self._load_json(resp)
            plan = resp.get("plan")
            if plan and isinstance(plan, list):
                if (
                    len(plan) == 0
                    or len(plan) == 1
                    and len(plan[0].replace("-", "")) == 0
                ):
                    self.staging_tool = {"name": "task_complete", "args": {}}
                    self.staging_response = resp
                    self.state = AgentStates.STOP
            else:
                if isinstance(resp, dict):
                    if "name" in resp:
                        resp = {"command": resp}
                    if "command" in resp:
                        self.staging_tool = resp["command"]
                        self.staging_response = resp
                        self.state = AgentStates.TOOL_STAGED
                    else:
                        self.state = AgentStates.IDLE
                else:
                    self.state = AgentStates.IDLE

            progress = resp.get("thoughts", {}).get("progress")
            if progress:
                if isinstance(plan, str):
                    self.progress += [progress]
                elif isinstance(progress, list):
                    self.progress += progress
            plan = resp.get("thoughts", {}).get("plan")
            if plan:
                if isinstance(plan, str):
                    self.plan = [plan]
                if isinstance(plan, list):
                    self.plan = plan
        except:
            pass
        self.history.append({"role": "user", "content": message})
        self.history.append(
            {
                "role": "assistant",
                "content": json.dumps(resp) if isinstance(resp, dict) else resp,
            }
        )
        return resp

    def _extract_json_with_gpt(self, s):
        func = "def convert_to_json(response: str) -> str:"
        desc = f"""Convert the given string to a JSON string of the form \n{json.dumps(DEFAULT_RESPONSE_FORMAT_, indent=4)}\nEnsure the result can be parsed by Python json.loads."""
        res = ai_function(func, desc, [s])
        return res

    def _load_json(self, s, try_gpt=True):
        if "Result: {" in s:
            s = s.split("Result: ", 1)[0]
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
                    try:
                        return ast.literal_eval(s + "}")
                    except:
                        if try_gpt:
                            s = self._extract_json_with_gpt(s)
                            try:
                                s = ast.literal_eval(s)
                                return s
                            except:
                                return self._load_json(s, try_gpt=False)
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
            resp = "Command name not provided. Make sure to follow the specified response format."
            self.history.append(
                {
                    "role": "system",
                    "content": resp,
                }
            )
            return resp
        tool_id = self.staging_tool["name"]
        args = self.staging_tool.get("args", {})
        if tool_id == "task_complete":
            resp = {"success": True}
        elif tool_id == "do_nothing":
            resp = {"response": "Nothing Done."}
        else:
            if "args" not in self.staging_tool:
                resp = "Command args not provided. Make sure to follow the specified response format."
                self.history.append(
                    {
                        "role": "system",
                        "content": resp,
                    }
                )
                return resp
            kwargs = self.staging_tool["args"]
            found = False
            for k, tool in self.tools.items():
                if k == tool_id:
                    found = True
                    break
            if not found:
                resp = f'Command "{tool_id}" does not exist.'
                self.history.append({"role": "system", "content": resp})
                return resp
            try:
                resp = tool.run(**kwargs)
            except Exception as e:
                resp = f'Command "{tool_id}" failed with error: {e}'
                self.history.append(
                    {
                        "role": "system",
                        "content": resp,
                    }
                )
                return resp
        self.history.append(
            {
                "role": "system",
                "content": f'Command "{tool_id}" with args {json.dumps(args)} returned:\n{json.dumps(resp)}',
            }
        )
        return resp

    def clear_state(self):
        self.staging_tool = None
        self.staging_response = None
        self.tool_response = None
        self.progress = []
        self.state = AgentStates.START
        self.history.clear()
        self.sub_agents.clear()
        self.memory.clear()
        self.plan.clear()

    def header_prompt(self):
        prompt = []
        prompt.append(self.persona_prompt())
        if self.tools:
            prompt.append(self.tools_prompt())
        if self.goals:
            prompt.append(self.goals_prompt())
        if self.constraints:
            prompt.append(self.constraints_prompt())
        if self.plan:
            prompt.append(self.plan_prompt())
        if self.progress:
            prompt.append(self.progress_prompt())
        return "\n".join(prompt) + "\n"

    def persona_prompt(self):
        return f"You are {self.name}, {self.description}."

    def progress_prompt(self):
        prompt = []
        prompt.append(f"PROGRESS SO FAR:")
        for i, p in enumerate(self.progress):
            prompt.append(f"{i + 1}. DONE - {p}")
        return "\n".join(prompt) + "\n"

    def plan_prompt(self):
        plan = "\n".join(self.plan)
        return f"CURRENT PLAN:\n{plan}\n"

    def goals_prompt(self):
        prompt = []
        prompt.append(f"GOALS:")
        for i, g in enumerate(self.goals):
            prompt.append(f"{i + 1}. {g}")
        return "\n".join(prompt) + "\n"

    def constraints_prompt(self):
        prompt = []
        prompt.append(f"CONSTRAINTS:")
        for i, c in enumerate(self.constraints):
            prompt.append(f"{i + 1}. {c}")
        return "\n".join(prompt) + "\n"

    def tools_prompt(self):
        prompt = []
        prompt.append("Commands:")
        for i, tool in enumerate(self.tools.values()):
            tool.agent = self
            prompt.append(f"{i + 1}. {tool.prompt()}")
        task_complete_command = {
            "name": "task_complete",
            "description": "Execute when all tasks are completed. This will terminate the session.",
            "args": {},
            "response_format": {"success": "true"},
        }
        do_nothing_command = {
            "name": "do_nothing",
            "description": "Do nothing.",
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

    def config(self, include_state=True):
        cfg = {
            "class": self.__class__.__name__,
            "type": "agent",
            "name": self.name,
            "description": self.description,
            "goals": self.goals[:],
            "constraints": self.constraints[:],
            "state": self.state,
            "model": self.model.config(),
            "temperature": self.temperature,
            "tools": [tool.config() for tool in self.tools.values()],
        }
        if include_state:
            cfg.update(
                {
                    "progress": self.progress[:],
                    "plan": self.plan[:],
                    "sub_agents": {
                        k: (v[0].config(), v[1]) for k, v in self.sub_agents.items()
                    },
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
        agent.constraints = config["constraints"][:]
        agent.state = config["state"]
        agent.temperature = config["temperature"]
        agent.model = model_from_config(config["model"])
        agent.tools = {tool.id: tool for tool in map(tool_from_config, config["tools"])}
        agent.progress = config.get("progress", [])
        agent.plan = config.get("plan", [])
        agent.sub_agents = {
            k: (cls.from_config(v[0]), v[1])
            for k, v in config.get("sub_agents", {}).items()
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

    def cli(self, continuous=False):
        cli(self, continuous=continuous)
