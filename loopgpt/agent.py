from loopgpt.constants import DEFAULT_CONSTRAINTS, RESPONSE_FORMAT, DEFAULT_EVALUATIONS
from loopgpt.tools.browser import Browser
from loopgpt.tools.code import ExecutePythonFile
from loopgpt.tools.filesystem import FileSystemTools
from loopgpt.tools.shell import Shell
from loopgpt.tools.agent_manager import AgentManagerTools
from loopgpt.models.openai_ import chat


class Agent:
    def __init__(self, name="LoopGPT", model="gpt-3.5-turbo"):
        self.name = name
        self.model = model
        self.sub_agents = {}
        self.tools = {}
        self.constraints = set(DEFAULT_CONSTRAINTS)
        self.evaluations = set(DEFAULT_EVALUATIONS)
        self.response_format = RESPONSE_FORMAT
        self.history = []
        self._register_default_tools()

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

    def add_constraint(self, constraint: str):
        self.constraints.add(constraint)

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

    def add_evaluation(self, evaluation):
        self.evaluations.add(evaluation)

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
            f"You should only respond in JSON format as described below\nResponse Format:\n{self.response_format}\nEnsure the response can be parsed by Python json.loads."
        )
        return "\n".join(prompt)
