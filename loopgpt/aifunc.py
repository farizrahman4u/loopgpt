from typing import Any, Dict, List
from functools import wraps
import loopgpt
import inspect
import ast
import re

from loopgpt.agent import Agent, empty_agent
from loopgpt.tools.base_tool import BaseTool
from loopgpt.constants import AgentStates

import loopgpt.agent


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


def set_agent_tools(agent: Agent, tools: List[BaseTool]):
    for tool_cls in tools:
        tool = tool_cls()
        agent.tools[tool.id] = tool


def create_analyzer_agent(func_prompt, tools, args_prompt, **agent_kwargs):
    agent = empty_agent(**agent_kwargs)
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
    agent = empty_agent(**agent_kwargs)
    set_agent_tools(agent, tools)
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


class aifunc:
    """This class implements a decorator used to create AI functions. Functions decorated by ``@loopgpt.aifunc()`` need only have a valid
    function signature and docstring. The function can then be called normally, and the AI agent will emulate the function's execution and return a valid
    python object.

    :param tools: List of tools to be used by the agent to collect data. Defaults to ``None``.
    :type tools: List[BaseTool], optional

    An AI function is executed by an agent.
        - If an ``agent`` argument is passed to the decorated function, that agent will be used for execution.
        - If such an argument is not passed and the AI function is called in the ``with`` context of an agent, that agent will be used for execution.
        - If neither of the above conditions are met, a new agent will be created and used for execution.
            - The model and embedding provider to be used by this new agent can be passed as arguments to the decorated function:
                - ``model``: A :class:`~loopgpt.models.base.BaseModel` object.
                - ``embedding_provider``: A :class:`~loopgpt.embeddings.base.BaseEmbeddingProvider` object.
            - If these arguments are not passed and :func:`loopgpt.set_aifunc_args` has been called, the model and embedding provider
              passed to that function will be used globally.
            - If neither of the above conditions are met, the default model (GPT-3.5-Turbo) and embedding provider (OpenAIEmbeddingProvider) will be used.

    .. note::
        Always create agents using :func:`loopgpt.empty_agent <loopgpt.agent.empty_agent>` when using them in conjunction with AI functions.

    Examples:

        >>> @loopgpt.aifunc()
        ... def shakespearify(text: str) -> str:
        ...     '''Applies a shakespearian style to the given text and returns it.
        ...
        ...     Args:
        ...         text (str): Text to apply shakespearian style to.
        ...
        ...     Returns:
        ...         str: Text with shakespearian style.
        ...
        ...     '''
        ...
        >>> shakespearify("Hey man, how you doin? I was just heading to the store ya know")
        'Hark, good sir! How art thou faring? I was but making my way to the market, dost thou know.'

        >>> @loopgpt.aifunc(tools=[GoogleSearch])
        ... def find_age(celeb: str) -> int:
        ...     '''Searches Google for the celebrity's age and returns it.
        ...
        ...     Args:
        ...         celeb (str): Name of the celebrity.
        ...
        ...     Returns:
        ...         int: Age of the celebrity.
        ...
        ...     '''
        ...
        >>> find_age("Robert De Niro") + find_age("Al Pacino")
        162

        Using AI functions in the ``with`` context of an agent:

        >>> import loopgpt
        >>> from loopgpt.tools import GoogleSearch, Browser
        >>> @loopgpt.aifunc()
        ... def outline_maker(topic: str) -> str:
        ...     '''Writes an outline of the given topic.
        ...
        ...     Args:
        ...         topic (str): Topic to write an outline about.
        ...
        ...     Returns:
        ...         str: Outline of the topic.
        ...
        ...     '''
        ...
        >>> search = GoogleSearch()
        >>> browser = Browser()
        >>> agent = loopgpt.empty_agent()
        >>>
        >>> with agent:    # the agent will "watch" the searching and the browsing in the with block
        >>>     results, links = search("SVB Banking Crisis")
        >>>     for i in range(2):
        >>>         browser(links[i])
        >>>
        >>>     outline = outline_maker("SVB Banking Crisis")    # this AI function can access the memory of 'agent'
        >>> print(outline)
        1. The collapse of Silicon Valley Bank (SVB) and its impact on the crypto market.
        2. The closure of SVB leading to a bank run at Signature Bank.
        3. Regulators intervening to prevent a larger financial meltdown.
        4. The FDIC attempting to make all depositors whole, regardless of insurance.
        5. Government investigation into SVB's failure and stock sales by financial officers.
        6. Moody's downgrading the outlook on the U.S. banking system.
        7. Other banks being placed under review for a downgrade.
        8. Proposed legislation by Sen. Elizabeth Warren and Rep. Katie Porter to strengthen bank regulations.
        9. Banking crisis reaching Europe with Credit Suisse losing share value.
    """

    model = None
    embedding_provider = None

    def __init__(self, tools: List = []):
        self.tools = tools

    def __call__(self, func):
        @wraps(func)
        def inner(*args, model=None, embedding_provider=None, **kwargs):
            sig = inspect.signature(func)

            agent_kwargs = {
                "model": model or aifunc.model,
                "embedding_provider": embedding_provider or aifunc.embedding_provider,
            }
            agent = kwargs.pop("agent", loopgpt.agent.ACTIVE_AGENT)

            if agent is None:
                agent = empty_agent(**agent_kwargs)

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
    Returns the updated function sequence.

    Args:
        function_sequence (List[Dict[str, Any]]): List of dictionary of function sequence.
        execution_history (List[Dict[str, Any]]): List of execution history.

    Returns:
        List[Dict[str, Any]]: Updated function sequence.

    """
