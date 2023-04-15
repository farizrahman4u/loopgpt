from loopgpt.tools.browser import Browser
from loopgpt.tools.code import ExecutePythonFile
from loopgpt.tools.filesystem import FileSystemTools
from loopgpt.tools.shell import Shell
from loopgpt.tools.agent_manager import AgentManagerTools
from loopgpt.tools import deserialize as deserialize_tool
from loopgpt.models.openai_ import chat


class Agent:
    def __init__(self, name="LoopGPT", model="gpt-3.5-turbo"):
        self.name = name
        self.model = model
        self.sub_agents = {}
        self.tools = {}
        self.constraints = set()
        self.evaluations = set()
        self.history = []
        self._register_default_tools()
        self._add_default_constraints()
        self._add_default_evaluations()

    def _default_tools(self):
        yield Shell()
        yield Browser()
        yield ExecutePythonFile()
        for tool_cls in FileSystemTools:
            yield tool_cls()
        for tool_cls in AgentManagerTools:
            yield tool_cls(self.sub_agents)

    def register_tool(self, tool):
        self.tools[tool.id] = tool

    def _register_default_tools(self):
        for tool in self._default_tools():
            self.register_tool(tool)

    def _default_constraints(self):
        yield "~4000 word limit for short term memory. Your short term memory is short, so immediately save important information to files."
        yield "If you are unsure how you previously did something or want to recall past events, thinking about similar events will help you remember."
        yield "No user assistance"
        yield 'Exclusively use the commands listed in double quotes e.g. "command_name"'

    def add_constraint(self, constraint: str):
        self.constraints.add(constraint)

    def _add_default_constraints(self):
        for constraint in self._default_constraints():
            self.add_constraint(constraint)

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

    def clear_history(self):
        self.history.clear()

    def clear_sub_agents(self):
        self.sub_agents.clear()

    def clear_state(self):
        self.clear_history()
        self.clear_sub_agents()

    def _response_format(self):
        return {
            "thoughts": {
                "text": "thought",
                "reasoning": "reasoning",
                "plan": "- short bulleted\n- list that conveys\n- long-term plan",
                "criticism": "constructive self-criticism",
                "speak": "thoughts summary to say to user",
            },
            "command": {"name": "command name", "args": {"arg name": "value"}},
        }

    def _default_evaluations(self):
        yield "Continuously review and analyze your actions to ensure you are performing to the best of your abilities."
        yield "Constructively self-criticize your big-picture behavior constantly."
        yield "Reflect on past decisions and strategies to refine your approach."
        yield "Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps."

    def add_evaluation(self, evaluation):
        self.evaluations.add(evaluation)

    def _add_default_evaluations(self):
        for evaln in self._default_evaluations():
            self.add_evaluation(evaln)

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
        prompt.append(
            f"You should only respond in JSON format as described below\nResponse Format:\n{self._response_format()}\nEnsure the response can be parsed by Python json.loads."
        )
        return "\n".join(prompt)

    def config(self, include_state=True):
        cfg = {
            "class": self.__class__.__name__,
            "name": self.name,
            "model": self.model,
            "tools": {k: v.serialize() for k, v in self.tools.items()},
            "constraints": self.constraints[:],
            'evaluations': self.evaluations[:],
            "response_format": self.response_format,
        }
        if include_state:
            cfg["sub_agents"] = {
                k: v.config() for k, v in self.sub_agents.items()
            }
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
        agent.sub_agents = {k: cls.from_config(v) for k, v in config.get("sub_agents", {}).items()}
        agent.history = config.get("history", [])
