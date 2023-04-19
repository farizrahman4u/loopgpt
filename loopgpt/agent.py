from loopgpt.constants import (
    DEFAULT_RESPONSE_FORMAT_,
    INIT_PROMPT,
    DEFAULT_AGENT_NAME,
    DEFAULT_AGENT_DESCRIPTION,
    NEXT_PROMPT,
    NEXT_PROMPT_SMALL,
)
from loopgpt.memory import from_config as memory_from_config
from loopgpt.models.openai_ import chat, count_tokens, get_token_limit
from loopgpt.tools import builtin_tools, from_config as tool_from_config
from loopgpt.tools.code import ai_function
from loopgpt.memory.local_memory import LocalMemory
from loopgpt.embeddings.openai_ import OpenAIEmbeddingProvider
from loopgpt.utils.spinner import spinner
from loopgpt.loops import cli


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
        self.history = []
        tools = [tool_type() for tool_type in builtin_tools()]
        self.tools = {tool.id: tool for tool in tools}
        self.staging_tool = None
        self.staging_response = None
        self.tool_response = None
        self.init_prompt = INIT_PROMPT
        self.next_prompt = NEXT_PROMPT

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
        prompt = [header, dtime]
        msgs = self._get_non_user_messages(10)
        relevant_memory = self.memory.get(str(msgs), 5) if len(msgs) > 5 else []
        memory_added = False
        if relevant_memory:
            # Add as many documents from memory as possible while staying under the token limit
            token_limit = 1500
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
            if relevant_memory:
                memory_added = True
                prompt.append(context)
        history = self._get_compressed_history()
        user_prompt = [{"role": "user", "content": user_input}] if user_input else []
        prompt = prompt[:2] + history + prompt[2:]
        token_limit = get_token_limit(self.model) - 1000  # 1000 reserved for response
        token_count = count_tokens(prompt + user_prompt, model=self.model)
        while history[:-1] and token_count > token_limit:
            history = history[1:]
            prompt.pop(2)
            token_count = count_tokens(prompt + user_prompt, model=self.model)
        if memory_added and len(prompt) > 4:
            sys_resp = prompt.pop(-2)
            agent_resp = prompt.pop(-2)
            prompt.append(agent_resp)
            prompt.append(sys_resp)
        prompt += user_prompt
        return prompt, token_count

    def _get_compressed_history(self):
        hist = self.history[:]
        system_msgs = [i for i in range(len(hist)) if hist[i]["role"] == "system"]
        for i in system_msgs[:-1]:
            entry = hist[i].copy()
            msg = entry["content"]
            if msg.startswith("Response from "):
                tool = msg[len("Response from ") :].split(":", 1)[0]
                entry["content"] = f"<Response from {tool}>"
                hist[i] = entry
        assist_msgs = [i for i in range(len(hist)) if hist[i]["role"] == "assistant"]
        for i in assist_msgs[:-1]:
            entry = hist[i].copy()
            try:
                respd = json.loads(entry["content"])
                thoughts = respd.get("thoughts")
                if thoughts:
                    thoughts.pop("reasoning", None)
                    thoughts.pop("speak", None)
                    thoughts.pop("criticism", None)
                    # if False and i < len(assist_msgs) - 2:
                    thoughts.pop("text", None)
                entry["content"] = json.dumps(respd, indent=2)
                hist[i] = entry
            except:
                pass
        user_msgs = [i for i in range(len(hist)) if hist[i]["role"] == "user"]
        for i in user_msgs:
            entry = hist[i].copy()
            msg = entry["content"]
            if msg in [self.next_prompt, self.init_prompt]:
                entry["content"] = NEXT_PROMPT_SMALL
                hist[i] = entry
        return hist

    @spinner
    def chat(self, message: Optional[str] = None, run_tool=False) -> Union[str, Dict]:
        if message is None:
            message = self.init_prompt
        if self.staging_tool:
            tool = self.staging_tool
            if run_tool:
                if tool.get("name") == "task_complete":
                    self.history.append(
                        {
                            "role": "system",
                            "content": "Completed all user specified tasks.",
                        }
                    )
                    message = ""
                output = self.run_staging_tool()
                self.tool_response = output
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
        token_limit = get_token_limit(self.model)
        maxt_tokens = max(1000, token_limit - token_count)
        resp = chat(
            full_prompt,
            model=self.model,
            max_tokens=maxt_tokens,
            temperature=self.temperature,
        )
        try:
            resp = self._load_json(resp)
            if "name" in resp:
                resp = {"command": resp}
            self.staging_tool = resp["command"]
            self.staging_response = resp
        except Exception as e:
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
        self.history.clear()
        self.sub_agents.clear()
        self.memory.clear()

    def header_prompt(self):
        prompt = []
        prompt.append(self.persona_prompt())
        if self.tools:
            prompt.append(self.tools_prompt())
        if self.goals:
            prompt.append(self.goals_prompt())
        return "\n".join(prompt) + "\n"

    def persona_prompt(self):
        return f"You are {self.name}, {self.description}."

    def goals_prompt(self):
        prompt = []
        prompt.append(f"GOALS:")
        for i, g in enumerate(self.goals):
            prompt.append(f"{i + 1}. {g}")
        return "\n".join(prompt) + "\n"

    def tools_prompt(self):
        prompt = []
        prompt.append("Commands:")
        for i, tool in enumerate(self.tools.values()):
            tool.agent = self
            prompt.append(f"{i + 1}. {tool.prompt()}")
        task_complete_command = {
            "name": "task_complete",
            "description": "Execute when all tasks are completed.",
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
            "model": self.model,
            "temperature": self.temperature,
            "tools": [tool.config() for tool in self.tools.values()],
        }
        if include_state:
            cfg.update(
                {
                    "sub_agents": {k: (v[0].config(), v[1]) for k, v in self.sub_agents.items()},
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
        agent.sub_agents = {
            k: (cls.from_config(v[0]), v[1]) for k, v in config.get("sub_agents", {}).items()
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
