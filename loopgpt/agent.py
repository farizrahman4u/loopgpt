from loopgpt.constants import (
    DEFAULT_RESPONSE_FORMAT_,
    INIT_PROMPT,
    DEFAULT_AGENT_NAME,
    DEFAULT_AGENT_DESCRIPTION,
    NEXT_PROMPT,
    DEFAULT_PROMPT_TEMPLATE,
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
from itertools import repeat
from contextlib import contextmanager

import openai
import json
import time
import ast
import re
import os

ACTIVE_AGENT = None


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
        Specify a :class:`~loopgpt.embeddings.base.BaseEmbeddingProvider` object to use other embedding providers.
    :type embedding_provider: :class:`~loopgpt.embeddings.base.BaseEmbeddingProvider`, optional
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
        tools=None,
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
        if tools is None:
            tools = [tool_type() for tool_type in builtin_tools()]
        else:
            tools = [tool_type() for tool_type in tools]
        self.tools = {tool.id: tool for tool in tools}
        self.staging_tool = None
        self.staging_response = None
        self.tool_response = None
        self.prompts = [INIT_PROMPT, NEXT_PROMPT]
        self.prompt_gen = self.next_prompt()
        self.prompt_template = DEFAULT_PROMPT_TEMPLATE
        self.progress = []
        self.plan = []
        self.constraints = []
        self.state = AgentStates.START
        self.memory_query = None
        self.additional_history = None

    def next_prompt(self):
        if self.prompts:
            yield from self.prompts
            yield from repeat(self.prompts[-1])
        else:
            yield from repeat("")

    def _get_non_user_messages(self, n):
        msgs = [
            msg
            for msg in self.history
            if msg["role"] != "user"
            and not (msg["role"] == "system" and "do_nothing" in msg["content"])
        ]
        return msgs[-n - 1 :]

    def get_full_prompt(self, user_input: str = ""):
        sections = re.findall(r"<(.*)>", self.prompt_template)
        user_prompt = [{"role": "user", "content": user_input}]
        # history = self.history[:]
        history = self._get_compressed_history()
        relevant_memory = []
        for section in sections:
            if section == "HEADER":
                header = {"role": "system", "content": self.header_prompt()}
                dtime = {
                    "role": "system",
                    "content": f"The current time and date is {time.strftime('%c')}",
                }
            elif section.startswith("MEMORY"):
                if self.memory_query:
                    memory_query = self.memory_query
                else:
                    n = None
                    if ":" in section:
                        section, n = section.split(":")
                        n = int(n)
                    mem_source = self._get_non_user_messages(n) + user_prompt
                    memory_query = "\n".join([hist["content"] for hist in mem_source])
                relevant_memory = self.memory.get(memory_query, 10)

        def _msgs():
            updated_msgs = []
            for section in sections:
                if section == "HEADER":
                    updated_msgs += [header, dtime]
                if section.startswith("HISTORY"):
                    updated_msgs += history[:]
                elif section.startswith("MEMORY"):
                    if relevant_memory:
                        memstr = "\n".join(relevant_memory)
                        context = {
                            "role": "system",
                            "content": (
                                f"Remember the following things in your memory:"
                                + "\n=============================MEMORY=============================\n"
                                + f"\n{memstr}\n"
                                + "================================================================\n"
                            ),
                        }
                        updated_msgs.append(context)
                elif section == "USER_INPUT":
                    updated_msgs += user_prompt
            return updated_msgs

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

    def _get_compressed_history(self):
        history = self._get_non_user_messages(30)
        maxtokens = self.model.get_token_limit()
        while True:
            message = [
                {
                    "role": "user",
                    "content": (
                        f"Please summarize this conversation for me:\n{history}\n\nImportant Details and Results:"
                        + "\n- Include key findings from the research and data collection phases.\n- Highlight important commands"
                        + "executed and their results.\n\nKey Highlights:\n- Summarize the main points of the conversation in bullet points."
                        + "\n- Focus on relevant information and filter out redundant exchanges.\n\nAdditional Context:\n- Provide any relevant links"
                        + " or references mentioned during the conversation.\n\nPlease ensure the summary accurately captures the essential aspects of"
                        + " the task and includes details that are crucial for understanding the context and progress.\n\nThank you!"
                    ),
                }
            ]
            ntokens = self.model.count_tokens(message)
            if ntokens < maxtokens:
                break
            else:
                history.pop(0)

        if len(history) == 0:
            history = []
        else:
            history_summary = self.model.chat(message)
            history = [{"role": "system", "content": history_summary}]
        if self.additional_history:
            history += [
                {"role": role, "content": content}
                for role, content in self.additional_history.items()
            ]
        return history

    def get_full_message(self, message: Optional[str]):
        return next(self.prompt_gen) + "\n\n" + (message or "")

    def _default_response_callback(self, resp):
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
            return resp
        except:
            raise

    @spinner
    def chat(
        self, message: Optional[str] = None, run_tool=False, response_callback=-1
    ) -> Optional[Union[str, Dict]]:
        if response_callback == -1:
            response_callback = self._default_response_callback
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
        # print("================================")
        # print(full_prompt)
        # print("================================")
        resp = self.model.chat(
            full_prompt,
            max_tokens=max_tokens,
            temperature=self.temperature,
        )
        if response_callback:
            resp = response_callback(resp)
        if self.state == AgentStates.START:
            self.state = AgentStates.IDLE
        self.history.append({"role": "user", "content": message})
        self.history.append(
            {
                "role": "assistant",
                "content": json.dumps(resp) if isinstance(resp, dict) else str(resp),
            }
        )
        return resp

    def _extract_json_with_gpt(self, s):
        func = "def convert_to_json(response: str) -> str:"
        desc = f"""Convert the given string to a JSON string of the form \n{json.dumps(DEFAULT_RESPONSE_FORMAT_, indent=4)}\nEnsure the result can be parsed by Python json.loads."""
        res = ai_function(func, desc, [s], self.model)
        return res

    def _load_json(self, s, try_gpt=True):
        if "Result: {" in s:
            s = s.split("Result: ", 1)[0]
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

    def tools_prompt(self, extras=False):
        prompt = []
        prompt.append("The following commands are already defined for you:")
        for i, tool in enumerate(self.tools.values()):
            tool.agent = self
            prompt.append(tool.prompt())

        if extras:
            task_complete_command = (
                f'def task_complete():\n\t"""{task_complete.__doc__}\n\t"""'.expandtabs(
                    4
                )
            )
            do_nothing_command = (
                f'def do_nothing():\n\t"""{do_nothing.__doc__}\n\t"""'.expandtabs(4)
            )
            prompt.append(task_complete_command)
            prompt.append(do_nothing_command)
        return "\n\n".join(prompt) + "\n"

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
            os.makedirs(os.path.dirname(file), exist_ok=True)
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

    def __enter__(self):
        """Sets this agent as the active agent globally. This allows any tools to add data to this agent's memory
        via a ``self.agent.memory.add`` call. In effect, the agent "watches" execution of tools in its with block.

        Example:

            >>> import loopgpt
            >>> from loopgpt.tools import GoogleSearch
            >>> agent = loopgpt.empty_agent()
            >>> search = GoogleSearch()
            >>> with agent:
            ...     # the following line will add the search results to the agent's memory
            ...     results, links = search("How to make a cake?")
            ...
            >>> print(agent.chat("Cake websites"))
            Sure! Here are eight websites that offer cake recipes and inspiration:
            1. Better Homes & Gardens - How to Make a Cake from Scratch That Looks Like It's From a Bakery: [Link](https://www.bhg.com/recipes/how-to/bake/how-to-make-a-cake/)
            2. Food Network - Basic Vanilla Cake Recipe: [Link](https://www.foodnetwork.com/recipes/food-network-kitchen/basic-vanilla-cake-recipe-2043654)
            3. ABCya! - Make a Cake: [Link](https://www.abcya.com/games/make-a-cake)
            4. Allrecipes - Simple White Cake Recipe: [Link](https://www.allrecipes.com/recipe/17481/simple-white-cake/)
            5. The Kitchn - How To Make a Cake from Scratch: [Link](https://www.thekitchn.com/how-to-make-a-cake-from-scratch-224370)
            6. House & Garden - Vanilla Cake Recipe: [Link](https://www.houseandgarden.co.uk/recipe/simple-vanilla-cake-recipe)
            7. RecipeTin Eats - My very best Vanilla Cake - stays moist 4 days!: [Link](https://www.recipetineats.com/my-very-best-vanilla-cake/)
            8. Times of India - How to Make Cake at Home: Homemade Cake Recipe: [Link](https://recipes.timesofindia.com/us/recipes/homemade-cake/rs54404412.cms)
        """
        global ACTIVE_AGENT
        if ACTIVE_AGENT:
            self._initial_active_agent = ACTIVE_AGENT
        ACTIVE_AGENT = self
        return self

    def __exit__(self, *args, **kwargs):
        """Resets the active agent to ``None``."""
        global ACTIVE_AGENT
        if hasattr(self, "_initial_active_agent"):
            ACTIVE_AGENT = self._initial_active_agent
        else:
            ACTIVE_AGENT = None

    @contextmanager
    def query(self, query):
        """Set a query for the agent's memory. This gives more control over what the agent remembers while generating responses.

        :param query: A query to filter the agent's memory by.
        :type query: str
        """
        try:
            self.memory_query = query
            yield
        finally:
            self.memory_query = None

    @contextmanager
    def complete(self, history):
        """Add additional history to the agent. This is useful for creating custom scenarios for the agent to respond to.

        :param history: A list of dictionaries with a key ``"system"``,  ``"assistant"`` or ``"user"`` and a value of the text to add to the agent's history.
        :type history: list
        """
        try:
            self.additional_history = history
            yield
        finally:
            self.additional_history = None


def empty_agent(**agent_kwargs):
    """Create an empty agent. Always use this function to create a new agent for use in conjunction with AI functions.
    Creating agents with the :class:`Agent` class directly is reserved for CLI applications.

    All parameters accepted by :class:`Agent` are accepted by this function.
    """
    agent = Agent(**agent_kwargs)
    agent.prompts = []
    agent.state = AgentStates.IDLE
    agent.tools = agent.tools if agent_kwargs.get("tools") else {}
    agent.goals = []
    agent.constraints = []
    agent.plan = []
    agent.progress = []
    agent.temperature = 0
    agent._default_response_callback = lambda x: x
    return agent


def task_complete():
    """Mark the current task as complete.

    Returns:
        None
    """


def do_nothing():
    """No-op command.

    Returns:
        None
    """
