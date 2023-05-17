from typing import Any, Dict, List
import loopgpt
import inspect
import ast

from loopgpt.constants import AgentStates
from loopgpt.tools import Browser
from loopgpt.models import BaseModel
from loopgpt.summarizer import Summarizer
from duckduckgo_search import ddg

def create_empty_agent(**agent_kwargs):
    agent = loopgpt.Agent(**agent_kwargs)
    agent.init_prompt = ""
    agent.next_prompt = ""
    agent.state = AgentStates.IDLE
    agent.tools = {}
    agent.goals = []
    agent.constraints = []
    agent.plan = []
    agent.progress = []
    agent.temperature = 0
    return agent

def get_func_prompt(func, sig):
    sig_and_doc = f'def {func.__name__}{sig}:\n\t"""{func.__doc__}\n\t"""'.expandtabs(4)
    return f"a python function with the following signature:\n```\n{sig_and_doc}\n```\n\n"

def get_args_prompt(sig, args, kwargs):
    params = sig.parameters
    positional_args = [arg for arg, p in params.items() if p.kind == p.POSITIONAL_OR_KEYWORD or p.kind == p.POSITIONAL_ONLY]
    
    str_fmt = '"""\n{}\n"""'
    args_str = "\n\n".join([f"{positional_args[i]}:\n\n{str_fmt.format(arg) if isinstance(arg, str) else arg}" for i, arg in enumerate(args)])
    kwargs_str = "\n\n".join([f"{key}:\n\n{value}" for key, value in kwargs.items()])

    return f"Arguments:\n\n{args_str}\n\n{kwargs_str}"

def main_response_callback(resp, return_annotation):
    if return_annotation == str:
        resp = resp.strip('"""').strip('"')
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
        return ast.literal_eval(resp)
    except ValueError:
        print("Command parsing failed.")
        return []

def _google_search(query: str) -> str:
    from googleapiclient.discovery import build
    import os

    service = build("customsearch", "v1", developerKey=os.getenv("GOOGLE_API_KEY"))
    results = (
        service.cse()
        .list(q=query, cx=os.getenv("GOOGLE_CX_ID"), num=2)
        .execute()
        .get("items", [])
    )
    results_ = []

    links_and_titles_ = []

    for i, result in enumerate(results):
        links_and_titles_.append(f"{i + 1}. {result['link']}: {result['title']}")
        results_.append(f"{i + 1}. {result['link']}\n\n{result['title']}\n\n{result['snippet']}\n")

    links_and_titles = "\n".join(links_and_titles_)
    results = "\n".join(results_)
    return results, links_and_titles

def _duckduckgo_search(query: str) -> str:
    results = ddg(query, max_results=2)
    results_ = []

    links_and_titles_ = []

    for i, result in enumerate(results):
        links_and_titles_.append(f"{i + 1}. {result['href']}: {result['title']}")
        results_.append(f"{i + 1}. {result['href']}\n\n{result['title']}\n\n{result['body']}\n")

    links_and_titles = "\n".join(links_and_titles_)
    results = "\n".join(results_)
    return results, links_and_titles

def google_search(query: str, model: BaseModel) -> str:
    """This is an atomic search function. It searches for the query on Google and returns the titles and links of the top results.
    
    Args:
        query (str): Query to search for.
    
    Returns:
        str: Result of the query.

    """
    try:
        results, links_and_titles = _google_search(query)
    except:
        results, links_and_titles = _duckduckgo_search(query)

    summarizer = Summarizer()
    summarizer._model = model
    results = summarizer.summarize(results, query)[0]

    retval = f"Google Search summary for \"{query}\": " + results + "\n" + "Links found that you may browse:\n" + links_and_titles + "\n"

    return retval


def browser(url: str, query: str, model: BaseModel) -> str:
    """This is an atomic browser function. It opens the url and finds the answer for the query.
    
    Args:
        url (str): URL to open.
        query (str): Query to search for.
    
    Returns:
        str: Query result extracted from the url.

    """

    browser = Browser()
    browser.summarizer._model = model

    resp = browser.run(url, query)
    if isinstance(resp, dict):
        retval = resp["text"]
    else:
        retval = resp
    
    retval = f"Browser result for \"{query}\" from \"{url}\": " + "\n" + retval + "\n"
    return retval

def create_analyzer_agent(func_prompt, args_prompt, **agent_kwargs):
    agent = create_empty_agent(**agent_kwargs)
    agent.name = "Function Analyzer"
    agent.description = f"and you have to imagine you are {func_prompt}"
    if args_prompt:
        agent.description += f"with {args_prompt}"
    agent.state = AgentStates.START
    agent.init_prompt = (
        "Do you need any external or real-time data to execute the function?"
        + "\nStrictly Respond with `yes` or `no` only."
        + "\n\nYour response is to be directly parsed, so please do not include any other text in your response.\n"
    )
    agent.next_prompt = (
        "Do you need more information than what is available in your memory to execute the function?\n"
        + "Strictly respond with `yes` or `no` only.\n\n"
        + "Your response is to be directly parsed, so please do not include any other text in your response.\n"
    )
    return agent

def create_data_collector_agent(func_prompt, args_prompt, **agent_kwargs):
    agent = create_empty_agent(**agent_kwargs)
    agent.name = "Execution Data Collector"
    agent.description = f"and you have to make a plan to collect relevant data for the successful execution of {func_prompt}"
    if args_prompt:
        agent.description += f"with {args_prompt}"
    agent.state = AgentStates.START
    agent.init_prompt = (
        "You have access to the following helper functions for collecting data:\n\n"
        + f"1. `google_search`: \n\t{google_search.__doc__}\n".expandtabs(4)
        + f"2. `browser`: \n\t{browser.__doc__}\n".expandtabs(4)
        + "Respond with a sequence of functions as a list of dictionaries containing the following keys:\n"
        + "1. `function` - Name of the function to use.\n"
        + "2. `args` - Dictionary of arguments to pass to the function.\n"
        + "Return an empty list if the execution does not require any data collection.\n"
        + "\nYour response is to be directly parsed, so please do not include any other text in your response.\n"
    )
    agent.next_prompt = (
        "You now have data in your memory. Do you need more data for the function? Continue data collection only if necessary. Return an empty list to terminate data collection.\n"
        + agent.init_prompt
    )
    return agent

def expand_placeholders(function_sequence: List[Dict[str, Any]], execution_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """This is a function that updates the function sequence by replacing placeholders with values from the execution history.

    Args:
        function_sequence (List[Dict[str, Any]]): List of dictionary of function sequence.
        execution_history (list): List of execution history.
    
    Returns:
        dict: Updated dictionary of function sequence.

    """

def aifunc(**agent_kwargs):
    def decorator(func):
        def inner(*args, **kwargs):
            sig = inspect.signature(func)

            internet = agent_kwargs.pop("internet", True)
            agent = create_empty_agent(**agent_kwargs)

            agent.name = func.__name__
            func_prompt = get_func_prompt(func, sig)
            agent.description = func_prompt + "Your response should only contain your `return` value."

            args_str = get_args_prompt(sig, args, kwargs)
            if args_str == "":
                args_str = "Arguments:\n\nThis function does not take any arguments."

            if internet:
                analyzer = create_analyzer_agent(func_prompt, args_str, **agent_kwargs)
                collector = create_data_collector_agent(func_prompt, args_str, **agent_kwargs)
                update_seq = aifunc(**agent_kwargs, internet=False)(expand_placeholders)

                analyzer.memory = agent.memory
                collector.memory = agent.memory
                
                req_data = analyzer.chat(response_callback=None).lower().strip().strip(".")

                max_iter_0 = 10
                while req_data == "yes" and max_iter_0 > 0:
                    commands = collector.chat(response_callback=collector_response_callback)
                    while commands:
                        command = commands[0]
                        funct = globals()[command["function"]]
                        resp = funct(**command["args"], model=agent.model)
                        agent.memory.add(resp)
                        last_command = f"You executed {command['function']} with args {command['args']} and got the following response: \n{resp}\n\n"
                        msg = {
                            "role": "system",
                            "content": last_command
                        }

                        collector.history.append(msg)
                        agent.history.append(msg)

                        if len(commands) > 1:
                            commands = update_seq(commands, last_command)
                        commands.pop(0)
                    req_data = analyzer.chat(response_callback=None).lower().strip().strip(".")
                    max_iter_0 -= 1

            resp = agent.chat(args_str + "\n\nYour response is to be directly parsed, so please do not include any other text in your response.\n", response_callback=None)

            return main_response_callback(resp, sig.return_annotation)
        return inner
    return decorator
