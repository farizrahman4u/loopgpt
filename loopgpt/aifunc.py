import loopgpt
import inspect
import ast

from loopgpt.constants import AgentStates

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

def aifunc(**agent_kwargs):
    def decorator(func):
        def inner(*args, **kwargs):
            agent = create_empty_agent(**agent_kwargs)
            agent.name = func.__name__
            sig = inspect.signature(func)
            sig_and_doc = f'def {func.__name__}{sig}:\n\t"""{func.__doc__}\n\t"""'.expandtabs(4)
            params = sig.parameters
            positional_args = [arg for arg, p in params.items() if p.kind == p.POSITIONAL_OR_KEYWORD or p.kind == p.POSITIONAL_ONLY]
            agent.description = f"a python function with the following signature:\n```\n{sig_and_doc}\n```\n\nYour response should only contain your `return` value."
            str_fmt = '"""\n{}\n"""'
            args_str = "\n\n".join([f"{positional_args[i]}:\n\n{str_fmt.format(arg) if isinstance(arg, str) else arg}" for i, arg in enumerate(args)])
            kwargs_str = "\n\n".join([f"{key}:\n\n{value}" for key, value in kwargs.items()])
            resp = agent.chat(f"Arguments:\n\n{args_str}\n\n{kwargs_str}")
            if sig.return_annotation == str:
                resp = resp.strip('"""').strip('"')
                return resp
            try:
                retval = ast.literal_eval(resp)
            except ValueError:
                try:
                    retval = ast.literal_eval(f'"{resp}"')
                except ValueError:
                    retval = resp
            return retval
        return inner
    return decorator
