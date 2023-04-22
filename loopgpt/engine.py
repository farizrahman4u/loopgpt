# The core execution engine
# Inspired by BabyAGI and Auto-GPT

from loopgpt.tools.base_tool import BaseTool
from loopgpt.tools import Browser, GoogleSearch, WriteToFile
from loopgpt.models.base import BaseModel
from loopgpt.models.openai_ import OpenAIModel
from loopgpt.embeddings.provider import BaseEmbeddingProvider
from loopgpt.embeddings.openai_ import OpenAIEmbeddingProvider
from loopgpt.memory.local_memory import LocalMemory
from typing import *
import ast
import json


DEFAULT_RESPONSE_FORMAT_ = {
    "text": "text to say to user.",
    "command": {"name": "next command in your plan", "args": {"arg name": "value"}},
}


class EngineState:
    START = "START"
    PLAN_PROPOSED = "PLAN_PROPOSED"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMMAND_PENDING = "COMMAND_PENDING"
    STOPPED = "STOPPED"


class Engine:
    def __init__(
        self,
        model: BaseModel = OpenAIModel(),
        embedding_provider: BaseEmbeddingProvider = OpenAIEmbeddingProvider(),
    ):
        self.model = model
        self.memory = LocalMemory(embedding_provider)
        self.objectives = ["Find 5 best headphones and write to file 'headphones.txt'"]
        self.tools = [Browser(), GoogleSearch(), WriteToFile()]
        self.reset()

    def reset(self):
        self.short_term_memory = []

    def _parse_numbered_list(self, s: str) -> List[str]:
        lines = s.split("\n")
        ret = []
        for line in lines:
            try:
                sp = line.split(". ")
                int(sp[0])
                ret.append(sp[1])
            except:
                pass
        return ret

    def _next_task(self):
        prompt = []
        prompt.append(
            "You are a command execution AI who executes exactly 1 command at time with NO USER ASSISTANCE to achieve the following goals:"
        )
        for i, objective in enumerate(self.objectives):
            prompt.append(f"{i+1}. {objective}")
        prompt.append("")
        prompt.append("Available commands:")
        for i, tool in enumerate(self.tools):
            prompt.append(f"{i+1}. {tool.prompt()}")
        task_complete_command = {
            "name": "task_complete",
            "description": "Execute when all the goals are achieved.",
            "args": {},
            "response_format": {"success": "true"},
        }
        prompt.append(f"{i + 2}. {json.dumps(task_complete_command)}")
        if self.short_term_memory:
            prompt.append("\nRemember following events from your past:")
            for i, mem in enumerate(self.short_term_memory):
                prompt.append(f"{i + 1}. {mem}")
        else:
            prompt.append("\nYou have not executed any commands yet.")
        prompt.append(
            "\nRespond exclusively in the following format: (Make sure it can be decoded with python json.loads())"
        )
        prompt.append(json.dumps(DEFAULT_RESPONSE_FORMAT_, indent=4))
        prompt = "\n".join(prompt) + "\n"
        msgs = [
            {"role": "system", "content": prompt},
        ]
        resp = self.model.chat(msgs, temperature=0)
        return json.loads(resp)

    def _execute_task(self, command):
        command_name = command["name"]
        args = command["args"]
        found = False
        resp = None
        for tool in self.tools:
            if tool.id == command_name:
                resp = tool.run(**args)
                found = True
                break
        if not found:
            raise Exception()
        self.short_term_memory.append(
            f'You executed command "{command_name}" with arguments {json.dumps(args)} which returned the following response:\n{json.dumps(resp, indent=2)}'
        )

    def _get_plan(self) -> List[str]:
        prompt = []
        prompt.append(
            "You are a planning AI. Create a plan to achieve the following objectives:"
        )
        for i, objective in enumerate(self.objectives):
            prompt.append(f"{i+1}. {objective}")
        prompt.append("You have access to the following tools:")
        for i, tool in enumerate(self.tools):
            prompt.append(f"{i+1}. {tool.prompt()}")
        prompt.append()
        prompt.append("")
        prompt.append("Return the plan as a numbered list, e.g,")
        prompt.append("1. Use <tool> to do task 1")
        prompt.append("2. Use <tool> to do task 2")
        prompt.append("3. Use <tool> to do task 3")
        prompt = "\n".join(prompt) + "\n"
        msgs = [
            {"role": "system", "content": prompt},
        ]
        resp = self.model.chat(msgs, temperature=0)
        tasks = self._parse_numbered_list(resp)
        return tasks

    def _persona_prompt(self, objectives: List[str]) -> str:
        prompt = []
        prompt.append("You are an AI with following objectives:")
        for i, objective in enumerate(objectives):
            prompt.append(f"{i+1}. {objective}")
        prompt.append("")
        return "\n".join(prompt) + "\n"

    def _tools_prompt(self, tools: List[BaseTool]) -> str:
        prompt = []
        prompt.append("You have the following tools:")
        for i, tool in enumerate(tools):
            prompt.append(f"{i+1}. {tool.prompt()}")
        prompt.append("")
        return "\n".join(prompt) + "\n"

    def _command_from_task_prompt(
        self, task: str, objectives: List[str], tools: List[BaseTool]
    ) -> dict:
        prompt = []
        prompt.append(self._persona_prompt(objectives))
        prompt.append(self._tools_prompt(tools))
        relevant_memory = self.memory.get(task, 10)
        if relevant_memory:
            prompt.append("You have the following memory relevant to the task:")
            for i, memory in enumerate(relevant_memory):
                prompt.append(f"{i+1}. {memory}")
        prompt.append("")
        prompt.append(task)
        prompt.append("")
        prompt.append(
            "(To use a tool, return the tool and arguments as a dictionary, e.g, {'name': '<tool name as string>', 'args': <tool arguments as dictionary>})"
        )
        return "\n".join(prompt) + "\n"

    def _get_command_from_task(
        self, task: str, objectives: List[str], tools: List[BaseTool]
    ) -> dict:
        prompt = self._command_from_task_prompt(task, objectives, tools)
        msgs = [
            {"role": "system", "content": prompt},
        ]
        resp = self.model.chat(msgs, temperature=0)
        try:
            command = ast.literal_eval(resp)
            name = command["name"]
            assert name in [tool.id for tool in tools]
        except:
            return False, resp
        return True, command

    def _command_denied_prompt(
        self,
        task: str,
        objectives: List[str],
        tools: List[str],
        proposed_command: dict,
        feedback: str,
    ) -> str:
        prompt = []
        prompt.append(self._persona_prompt(objectives))
        prompt.append(self._tools_prompt(tools))
        prompt.append(
            f'You suggested to execute the command `{proposed_command}` to complete the following task:\n"{task}"'
        )
        prompt.append(
            f'The user blocked the command with the following feedback:\n"{feedback}"'
        )
        prompt.append("Return a new command to run.")
        prompt.append(
            "Return the command as a dictionary, e.g, {'tool': '<tool name as string>', 'args': <tool arguments as dictionary>}"
        )
        return "\n".join(prompt) + "\n"

    def _plan_not_accpeted_prompt(
        self, objectives: List[str], tools: List[str], proposed_plan: List[str]
    ) -> str:
        prompt = []
        prompt.append(self._persona_prompt(objectives))
        prompt.append(self._tools_prompt(tools))
        prompt.append(f"You suggested the following plan to achieve your objectives:")
        prompt += proposed_plan
        prompt.append("The user rejected the plan.")
        prompt.append("Return a new plan.")
        prompt.append("Return the plan as a numbered list, e.g,")
        prompt.append("1. Use <tool> to do task 1")
        prompt.append("2. Use <tool> to do task 2")
        prompt.append("3. Use <tool> to do task 3")
        return "\n".join(prompt) + "\n"

    def _propose_another_plan(
        self, objectives: List[str], tools: List[str], proposed_plan: List[str]
    ) -> str:
        prompt = self._plan_not_accpeted_prompt(objectives, tools, proposed_plan)
        msgs = [
            {"role": "system", "content": prompt},
        ]
        resp = self.model.chat(msgs, temperature=0)
        tasks = self._parse_numbered_list(resp)
        return tasks

    def _propose_another_command(
        self,
        task: str,
        objectives: List[str],
        tools: List[str],
        proposed_command: dict,
        feedback: str,
    ) -> dict:
        prompt = self._command_denied_prompt(
            task, objectives, tools, proposed_command, feedback
        )
        msgs = [
            {"role": "system", "content": prompt},
        ]
        resp = self.model.chat(msgs, temperature=0)
        try:
            command = ast.literal_eval(resp)
            name = command["name"]
            assert name in [tool.id for tool in tools]
        except:
            raise Exception("Command generation failed.")
        return command

    def _handle_command_denied(self, task: str, command: dict, feedback: str):
        if feedback:
            entry = f'User denied running command `{command}` with following feedback to complete task "{task}":\n"{feedback}"'
        else:
            entry = (
                f'User denied running command `{command}` to complete task "{task}".'
            )
        # self.memory.add(entry, key=json.dumps({"task": task, "command": command['name'], "args": command["args"], "feedback": feedback}))
        self.memory.add(entry, key=task)

    def _handle_command_run(self, task: str, command: dict, resp: dict, feedback: str):
        self.completed_tasks.append((task, command, resp, feedback))
        if feedback:
            entry = f'User approved running command `{command}` with following feedback to complete task "{task}":\n"{feedback}"'
            entry += f"\nThe command returned the following response:\n```{resp}```"
        else:
            entry = f'User approved running command `{command}` to complete task "{task}". The command returned the following response:\n```{resp}```'

        # self.memory.add(entry, key=json.dumps({"task": task, "command": command['name'], "response": resp, "args": command["args"], "feedback": feedback}))
        self.memory.add(entry, key=task)

    def _task_generator_prompt(
        self,
        objectives: List[str],
        tools: List[BaseTool],
        tasks: List[str],
        completed_tasks: List[str],
    ) -> str:
        prompt = []
        prompt.append(self._persona_prompt(objectives))
        prompt.append(self._tools_prompt(tools))
        prompt.append(f"The last task you completed was: {self.pending_task}")
        prompt.append(
            f"You executed the following command to complete the task: `{self.pending_command}`"
        )
        prompt.append(
            f"The command returned the following response:\n```{self.pending_command_response}```"
        )
        # relevant_memory = self.memory.get(json.dumps({"task": self.pending_task, "command": self.pending_command['name'], "args": self.pending_command["args"], "response": self.pending_command_response}), 10)
        relevant_memory = self.memory.get(self.pending_task, 10)
        if relevant_memory:
            prompt.append("\nRemember the following events from your past:")
            for i, entry in enumerate(relevant_memory):
                prompt.append(f"{i + 1}. {entry}")
                prompt.append("")
        prompt.append("\nFollowing are completed tasks:\n")
        for i, task in enumerate(completed_tasks):
            prompt.append(f"{i + 1}. {task[0]}")
        prompt.append("")
        prompt.append("\nFollowing are incomplete tasks:\n")
        for i, task in enumerate(tasks):
            prompt.append(f"{i + 1}. {task}")
        prompt.append("")
        prompt.append(
            "Based on the command reponse, create new tasks that do not overlap with incomplete or completed tasks, if any, required to achieve your objectives."
        )
        prompt.append("Return the new tasks as a numbered list. e.g,")
        prompt.append("1. Use <tool> to do task 1")
        prompt.append("2. Use <tool> to do task 2")
        prompt.append("3. Use <tool> to do task 3")
        prompt.append(
            "\nReturn empty string if you do not want to create any new tasks."
        )
        prompt.append("Do not repeat completed tasks.")
        return "\n".join(prompt) + "\n"

    def _get_new_tasks(
        self,
        objectives: List[str],
        tools: List[BaseTool],
        tasks: List[str],
        completed_tasks: List[str],
    ) -> List[str]:
        return []
        prompt = self._task_generator_prompt(objectives, tools, tasks, completed_tasks)
        msgs = [
            {"role": "system", "content": prompt},
        ]
        resp = self.model.chat(msgs, temperature=0)
        tasks = self._parse_numbered_list(resp)
        return tasks

    def _reprioritize_tasks_prompt(
        self, objectives: List[str], tools: List[str], tasks: List[str]
    ) -> List[str]:
        prompt = []
        prompt.append(self._persona_prompt(objectives))
        prompt.append(self._tools_prompt(tools))  # maybe not needed
        prompt.append(
            "Reprioritize the following tasks without adding or removing items to achieve your objectives:"
        )
        tasks = [f"{i + 1}. {t}" for i, t in enumerate(tasks)]
        prompt += tasks
        prompt.append("Return the tasks as a numbered list. e.g,")
        prompt.append("1. Use <tool> to do task 1")
        prompt.append("2. Use <tool> to do task 2")
        prompt.append("3. Use <tool> to do task 3")
        return "\n".join(prompt) + "\n"

    def _reprioritize_tasks(
        self, objectives: List[str], tools: List[str], tasks: List[str]
    ) -> List[str]:
        return tasks
        prompt = self._reprioritize_tasks_prompt(objectives, tools, tasks)
        msgs = [
            {"role": "system", "content": prompt},
        ]
        resp = self.model.chat(msgs, temperature=0)
        new_tasks = self._parse_numbered_list(resp)
        return new_tasks

    def step(self, accept=True, feedback: str = ""):
        if self.state == EngineState.START:
            self.proposed_tasks = self._get_plan()
            self.state = EngineState.PLAN_PROPOSED
        elif self.state == EngineState.PLAN_PROPOSED:
            if accept:
                self.tasks = self.proposed_tasks[:]
                self.state = EngineState.PLANNED
                return
            else:
                new_plan = self._propose_another_plan(
                    self.objectives, self.tools, self.tasks
                )
                self.proposed_tasks = new_plan
                return
        elif self.state == EngineState.PLANNED:
            if not self.tasks:
                self.state = EngineState.STOPPED
                return
            next_task = self.tasks[0]
            is_command, resp = self._get_command_from_task(
                next_task, self.objectives, self.tools
            )
            self.tasks.pop(0)
            if is_command:
                command = resp
                self.state = EngineState.COMMAND_PENDING
                self.pending_task = next_task
                self.pending_command = command
            else:
                self.memory.add(resp)
                self.completed_tasks.append(next_task)
                self.state = EngineState.PLANNED
        elif self.state == EngineState.COMMAND_PENDING:
            if accept:
                for tool in self.tools:
                    if tool.id == self.pending_command["name"]:
                        resp = tool.run(**self.pending_command["args"])
                        self._handle_command_run(
                            self.pending_task, self.pending_command, resp, feedback
                        )
                        self.pending_command_response = resp
                        self.state = EngineState.RUNNING
                        return resp
                raise Exception("Tool not found.")
            else:
                self._handle_command_denied(
                    self.pending_task, self.pending_command, feedback
                )
                new_command = self._propose_another_command(
                    self.pending_task,
                    self.objectives,
                    self.tools,
                    self.pending_command,
                    feedback,
                )
                self.pending_command = new_command
                return
        elif self.state == EngineState.RUNNING:
            new_tasks = self._get_new_tasks(
                self.objectives, self.tools, self.tasks, self.completed_tasks
            )
            tasks = self.tasks + new_tasks
            tasks = self._reprioritize_tasks(self.objectives, self.tools, tasks)
            self.proposed_tasks = tasks
            self.state = EngineState.PLAN_PROPOSED
        elif self.state == EngineState.STOPPED:
            return
