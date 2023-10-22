from loopgpt import empty_agent, Agent
from functools import wraps
from typing import List

import loopgpt.agent
import inspect

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

class Compiler(Agent):
    def __init__(self, func_prompt, tools, args_prompt, **agent_kwargs):
        super().__init__(
            "PyFunc Signature Compiler",
            (
                f"and you have to compile the given Python function signature into a set of tool calls: {func_prompt}"
            ),
            tools=tools, 
            prompts=[
                f"Assuming that the function is called with the following arguments: {args_prompt}"
                + "\nRespond with the tool calls (including parameters) to be made."
            ],
            **agent_kwargs
        )
        self._default_response_callback = lambda x: x


class ThoughtsCompiler(Agent):
    def __init__(self, thoughts_prompt, tools, **agent_kwargs):
        super().__init__(
            "ThoughtsCompiler",
            f"and you have to compile a thought process into a set of tool calls: {thoughts_prompt}",
            tools=tools,
            prompts=[
                "Strictly respond with a sequence of functions as a list of dictionaries containing the following keys:\n"
                + "1. `function` - Name of the function to use.\n"
                + "2. `args` - Dictionary of arguments to pass to the function.\n"
                + "\nYour response is to be directly parsed, so please do not include any other text in your response.\n"
            ],
            **agent_kwargs
        )
        self._default_response_callback = lambda x: x


class EagerExecutor(Agent):
    def __init__(self, func, func_prompt, args_prompt, command, tools, **agent_kwargs):
        super().__init__(
            func.__name__,
            func_prompt,
            tools=tools,
            prompts=[
                f"You are called with the following arguments: {args_prompt}"
                + "\nWhat will be your return value and why?",
                "Now respond only with your return value. Your response is to be directly parsed, strictly do not include any other text in your response.",
                "",
            ],
            **agent_kwargs
        )
        self.command = command
        self._default_response_callback = lambda x: x
    
    def chat(self, message=None):
        if self.command:
            command = self.command
            tool = self.tools[command["function"]]
            resp = tool.run(**command["args"])
            msg = {
                    "role": "system",
                    "content": f"You executed {command['function']} with {command['args']} and got the response: {resp}.",
                }
            self.history.append(msg)
            self.command = None
            super().chat() # Generate reasoning
        return super().chat(message=message) # Return result 


class ParameterResolver(Agent):
    def __init__(self, command, tools, **agent_kwargs):
        super().__init__(
            "ParameterResolver",
            f"and you have to return the arguments to be passed to the command: `{command['function']}`.",
            tools=tools,
            prompts=[
                "Strictly respond with a dictionary of arguments to be passed to the command.\n"
                + "If you don't yet know what arguments to pass, respond with an empty dictionary.\n"
                + "\nYour response is to be directly parsed, so please do not include any other text in your response.\n"
            ],
            **agent_kwargs
        )
        self._default_response_callback = lambda x: x


class Validator(Agent):
    def __init__(self, exec_history, thoughts, **agent_kwargs):
        super().__init__(
            "ExecValidator",
            (
                f"and you are to validate that this execution: {exec_history}"
                + f"\nmatches the thought process: {thoughts}"
            ),
            tools=[],
            prompts=[
                "Does the execution achieve the end goal of the thought process? Why? Is there anything missing?",
                "If everything looks good, respond 'OK'. If not, respond 'NOT OK'."
            ],
            **agent_kwargs
        )
        self._default_response_callback = lambda x: x
    
    def chat(self):
        self.reasoning = super().chat()
        status = super().chat()
        if status.lower() == "ok":
            return True
        return False

class Counselor(Agent):
    def __init__(self, thoughts, execution_history, failure_reason, tools, **agent_kwargs):
        super().__init__(
            "ExecCounselor",
            (
                f"You were executing a plan according to: {thoughts}\nusing the following commands: {execution_history}"
                + f"\nbut you failed after making partial progress because: {failure_reason}"
                + f"\nYou have to suggest how to continue from here."
            ),
            tools=tools,
            prompts=[
                "Respond with the tool calls (including parameters) to be made."
            ],
            **agent_kwargs
        )
        self._default_response_callback = lambda x: x


class aifunc:
    model = None
    embedding_provider = None

    def __init__(self, tools: List = []):
        self.tools = tools
    
    def __call__(self, func):
        @wraps(func)
        def inner(*args, agent=None, model=None, embedding_provider=None, **kwargs):
            sig = inspect.signature(func)
            agent_kwargs = {
                "model": model or aifunc.model,
                "embedding_provider": embedding_provider or aifunc.embedding_provider
            }
            agent = agent or loopgpt.agent.ACTIVE_AGENT
            if agent is None:
                agent = empty_agent(**agent_kwargs)
