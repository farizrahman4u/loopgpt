import loopgpt
import inspect
import ast

from loopgpt.constants import AgentStates
from loopgpt.tools import Browser
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

def response_callback(resp, return_annotation):
    if return_annotation == str:
        resp = resp.strip('"""').strip('"')
        return resp
    try:
        resp = ast.literal_eval(resp)
    except ValueError:
        try:
            resp = ast.literal_eval(f'"{resp}"')
        except ValueError:
            pass
    return resp


def google_search(query: str) -> str:
    """This is an atomic search function. It searches for the query on Google and returns the titles and links of the top results.
    
    Args:
        query (str): Query to search for.
    
    Returns:
        str: Result of the query.

    """
    results = []

    for i, result in enumerate(ddg(query, max_results=5)):
        results.append(f"Result {i+1}: {result['href']}\n\n{result['title']}\n\n{result['body']}\n\n")

    return "\n".join(results)

def browser(url: str, query: str) -> str:
    """This is an atomic browser function. It opens the url and finds the answer for the query.
    For simple searches, it is recommended to use the `google_search` function instead.
    
    Args:
        url (str): URL to open.
        query (str): Query to search for.
    
    Returns:
        str: Query result extracted from the url.

    """
    from loopgpt.models import AzureOpenAIModel

    browser = Browser()
    browser.summarizer._model = AzureOpenAIModel("loop-gpt-35-turbo")

    resp = browser.run(url, query)
    if isinstance(resp, dict):
        return resp["text"]
    else:
        return resp

def create_analyzer_agent(func_prompt, args_prompt, **agent_kwargs):
    agent = create_empty_agent(**agent_kwargs)
    agent.name = "Function Analyzer"
    agent.description = f"and you have to answer the user's questions about {func_prompt}"
    if args_prompt:
        agent.description += f"with {args_prompt}"
    agent.state = AgentStates.START
    agent.init_prompt = (
        "Does this function require any external or real-time data?"
        + "\nRespond with `yes` or `no` only."
        + "\n\nYour response is to be directly parsed, so please do not include any other text in your response.\n"
    )
    agent.next_prompt = (
        "Do you now have enough information in your memory to execute the function?\n"
        + "Respond with `yes` or `no` only.\n\n"
        + "Your response is to be directly parsed, so please do not include any other text in your response.\n"
    )
    return agent

def create_data_collector_agent(func_prompt, args_prompt, **agent_kwargs):
    agent = create_empty_agent(**agent_kwargs)
    agent.name = "Execution Data Collector"
    agent.description = f"and you have to collect relevant data for the successful execution of {func_prompt}"
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
        + "Return an empty list if the execution does not require any data collection.\n\n"
        + "\nYour response is to be directly parsed, so please do not include any other text in your response.\n"
    )
    agent.next_prompt = (
        "Continue your collection of data if required.\n"
        + agent.init_prompt
    )
    return agent

def aifunc(**agent_kwargs):
    def decorator(func):
        def inner(*args, **kwargs):
            sig = inspect.signature(func)

            agent = create_empty_agent(**agent_kwargs)
            agent.name = func.__name__
            func_prompt = get_func_prompt(func, sig)
            agent.description = func_prompt + "Your response should only contain your `return` value."

            args_str = get_args_prompt(sig, args, kwargs)
            if args_str == "":
                args_str = "Arguments:\n\nThis function does not take any arguments."

            analyzer = create_analyzer_agent(func_prompt, args_str, **agent_kwargs)
            collector = create_data_collector_agent(func_prompt, args_str, **agent_kwargs)

            analyzer.memory = agent.memory
            collector.memory = agent.memory

            req_collector = analyzer.chat(response_callback=None)
            print(req_collector)
            if req_collector == "yes":
                try:
                    commands = ast.literal_eval(collector.chat(response_callback=None))
                except Exception:
                    commands = []
                if commands:
                    funct = globals()[commands[0]["function"]]
                    resp = funct(**commands[0]["args"])
                    agent.memory.add(f"{commands[0]['function']} returned the following response:\n\n{resp}\n\n")

            resp = agent.chat(args_str + "\n\nYour response is to be directly parsed, so please do not include any other text in your response.\n", response_callback=None)

            return response_callback(resp, sig.return_annotation)
        return inner
    return decorator
