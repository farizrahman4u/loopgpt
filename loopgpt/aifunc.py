from typing import Any, Dict, List, Optional
from functools import partial, wraps
import loopgpt
import inspect
import ast
import re

from loopgpt.agent import Agent
from loopgpt.constants import AgentStates
from loopgpt.tools import Browser
from loopgpt.models import BaseModel
from loopgpt.summarizer import Summarizer
from duckduckgo_search import ddg
from loopgpt.tools.base_tool import BaseTool

import loopgpt.agent


def create_empty_agent(**agent_kwargs):
    agent = loopgpt.Agent(**agent_kwargs)
    agent.prompts = []
    agent.state = AgentStates.IDLE
    agent.tools = agent.tools if agent_kwargs.get("tools") else {}
    agent.goals = []
    agent.constraints = []
    agent.plan = []
    agent.progress = []
    agent.temperature = 0
    return agent


def get_func_prompt(func, sig):
    sig_and_doc = f'def {func.__name__}{sig}:\n\t"""{func.__doc__}\n\t"""'.expandtabs(4)
    return (
        f"a python function with the following signature:\n```\n{sig_and_doc}\n```\n\n"
    )


def get_args_prompt(sig, args, kwargs):
    params = sig.parameters
    positional_args = [
        arg
        for arg, p in params.items()
        if p.kind == p.POSITIONAL_OR_KEYWORD or p.kind == p.POSITIONAL_ONLY
    ]

    str_fmt = '"""\n{}\n"""'
    args_str = "\n\n".join(
        [
            f"{positional_args[i]}:\n\n{str_fmt.format(arg) if isinstance(arg, str) else arg}"
            for i, arg in enumerate(args)
        ]
    )
    kwargs_str = "\n\n".join([f"{key}:\n\n{value}" for key, value in kwargs.items()])

    return f"Arguments:\n\n{args_str}\n\n{kwargs_str}"


def main_response_callback(resp, return_annotation):
    if return_annotation == str:
        resp = resp.strip('"""').strip('"')
        return resp
    if str(return_annotation) == "typing.List[str]":
        try:
            resp = ast.literal_eval(resp)
        except:
            try:
                resp = [re.findall(r"'(.+)'", part)[0] for part in resp.split(",")]
            except:
                # at least return the string, smh
                return resp
        return resp
    try:
        resp = ast.literal_eval(resp)
    except ValueError:
        try:
            resp = ast.literal_eval(f'"{resp}"')
        except ValueError:
            print("Command parsing failed.")
    return resp


def collector_response_callback(resp):
    try:
        resp = resp[resp.find("[") : resp.rfind("]") + 1]
        return ast.literal_eval(resp)
    except ValueError:
        print("Command parsing failed.")
        return []


def create_analyzer_agent(func_prompt, tools, args_prompt, **agent_kwargs):
    agent = create_empty_agent(**agent_kwargs)
    set_agent_tools(agent, tools)
    agent.memory_query = func_prompt + "\n" + args_prompt
    agent.name = "Function Analyzer"
    agent.description = f"and you have to imagine you are {func_prompt}"
    if args_prompt:
        agent.description += f"with {args_prompt}"
    agent.state = AgentStates.IDLE
    agent.prompts = [
        "Do you need more information than what is available in your memory to execute the function?"
        + "Strictly respond with `yes` or `no` only.\n\n"
        + "Your response is to be directly parsed, so please do not include any other text in your response.\n"
    ]
    return agent


def create_data_collector_agent(func_prompt, tools, args_prompt, **agent_kwargs):
    agent = create_empty_agent(**agent_kwargs)
    set_agent_tools(agent, tools)
    # agent.memory_query = "How to make a pizza?"
    agent.name = "Execution Data Collector"
    agent.description = f"and you have to make a plan to collect relevant data for the successful execution of {func_prompt}"
    if args_prompt:
        agent.description += f"with {args_prompt}"
    agent.state = AgentStates.START
    init_prompt = (
        "Strictly respond with a sequence of functions as a list of dictionaries containing the following keys:\n"
        + "1. `function` - Name of the function to use.\n"
        + "2. `args` - Dictionary of arguments to pass to the function.\n"
        + "Return an empty list if the execution does not require any data collection.\n"
        + "\nYour response is to be directly parsed, so please do not include any other text in your response.\n"
    )
    agent.prompts = [
        init_prompt,
        "You now have data in your memory. Return an empty list to terminate data collection. Continue data collection only if neccessary.\n"
        + init_prompt,
    ]
    return agent


def set_agent_tools(agent: Agent, tools: List[BaseTool]):
    for tool_cls in tools:
        tool = tool_cls()
        agent.tools[tool.id] = tool


class aifunc:
    model = None
    embedding_provider = None
    memory = None

    def __init__(self, tools: List = []):
        self.tools = tools

    def __call__(self, func):
        @wraps(func)
        def inner(*args, model=None, embedding_provider=None, memory=None, **kwargs):
            sig = inspect.signature(func)

            agent_kwargs = {
                "model": model or aifunc.model,
                "embedding_provider": embedding_provider or aifunc.embedding_provider,
                "memory": memory or aifunc.memory,
            }
            agent = kwargs.pop("agent", loopgpt.agent.ACTIVE_AGENT)

            if agent is None:
                agent = create_empty_agent(**agent_kwargs)

            agent.name = func.__name__
            func_prompt = get_func_prompt(func, sig)
            agent.description = func_prompt

            if len(args) == 0 and len(kwargs) == 0:
                args_str = "Arguments:\n\nThis function does not take any arguments."
            else:
                args_str = get_args_prompt(sig, args, kwargs)

            if self.tools:
                analyzer = create_analyzer_agent(
                    func_prompt, self.tools, args_str, **agent_kwargs
                )
                collector = create_data_collector_agent(
                    func_prompt, self.tools, args_str, **agent_kwargs
                )

                analyzer.memory = agent.memory
                collector.memory = agent.memory

                commands = collector.chat(response_callback=collector_response_callback)
                req_data = True
                while commands and req_data:
                    command = commands[0]
                    if command["function"] == func.__name__:
                        commands.pop(0)
                        continue
                    tool = collector.tools[command["function"]]
                    resp = str(tool.run(**command["args"]))
                    last_command = str(
                        [
                            {
                                "function": command["function"],
                                "args": command["args"],
                                "response": resp,
                            }
                        ]
                    )

                    msg = {
                        "role": "system",
                        "content": f"You executed {command['function']} with {command['args']} and got the response: {resp}.",
                    }
                    collector.history.append(msg)
                    analyzer.history.append(msg)

                    if len(commands) > 1 and "<" in str(commands[1]["args"]):
                        new_commands = expand_placeholders(commands, last_command)
                        if new_commands:
                            commands = new_commands
                    commands.pop(0)
                    if len(commands) == 0:
                        req_data = analyzer.chat(response_callback=None)
                        if req_data == "yes":
                            commands = collector.chat(
                                response_callback=collector_response_callback
                            )

            resp = agent.chat(
                args_str
                + "Respond only with your return value. Your response is to be directly parsed, strictly do not include any other text in your response.",
                response_callback=None,
            )
            resp = main_response_callback(resp, sig.return_annotation)
            return resp

        return inner


@aifunc()
def expand_placeholders(
    function_sequence: List[Dict[str, Any]], execution_history: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """This is an atomic replace function. It replaces placeholders in angle brackets by analyzing the execution history. Return as is if no placeholders are present.
    Ensure URLs are full.

    Args:
        function_sequence (List[Dict[str, Any]]): List of dictionary of function sequence.
        execution_history (List[Dict[str, Any]]): List of execution history.

    Returns:
        List[Dict[str, Any]]: Updated function sequence.

    """
