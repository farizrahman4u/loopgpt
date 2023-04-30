HEADER = r"""
+------------------------------------------------------------+
| ██╗░░░░░░█████╗░░█████╗░██████╗░░██████╗░██████╗░████████╗ |
| ██║░░░░░██╔══██╗██╔══██╗██╔══██╗██╔════╝░██╔══██╗╚══██╔══╝ |
| ██║░░░░░██║░░░░██░░░░██║██████╔╝██║░░██╗░██████╔╝░░░██║░░░ |
| ██║░░░░░██║░░██║██║░░██║██╔═══╝░██║░░╚██╗██╔═══╝░░░░██║░░░ |
| ███████╗╚█████╔╝╚█████╔╝██║░░░░░╚██████╔╝██║░░░░░░░░██║░░░ |
| ╚══════╝░╚════╝░░╚════╝░╚═╝░░░░░░╚═════╝░╚═╝░░░░░░░░╚═╝░░░ |
+------------------------------------------------------------+
"""

from loopgpt.constants import (
    DEFAULT_AGENT_NAME,
    DEFAULT_AGENT_DESCRIPTION,
)
from colorama import Fore, Style

import os

LOOP_GPT = Fore.GREEN + "LoopGPT"
REASONING = Fore.LIGHTBLUE_EX + "REASONING"
PLAN = Fore.LIGHTYELLOW_EX + "PLAN"
PROGRESS = Fore.LIGHTRED_EX + "PROGRESS"
SPEAK = Fore.LIGHTGREEN_EX + "SPEAK"
COMMAND = Fore.LIGHTMAGENTA_EX + "NEXT_COMMAND"
SYSTEM = Fore.LIGHTYELLOW_EX + "SYSTEM"
INPUT_PROMPT = Fore.LIGHTYELLOW_EX + "Enter message: " + Style.RESET_ALL

profiles = {
    "loopgpt": LOOP_GPT,
    "reasoning": REASONING,
    "plan": PLAN,
    "progress": PROGRESS,
    "speak": SPEAK,
    "command": COMMAND,
    "system": SYSTEM,
}


def listed_prompt(speaker, message, item_kind):
    print_line(speaker, message)
    indent = " " * 4
    lst = []
    i = 1
    while True:
        print(
            indent + f"- {Fore.LIGHTBLUE_EX}{item_kind} {i} : {Style.RESET_ALL}", end=""
        )
        inp = input()
        if inp.lower().strip() == "exit":
            return -1
        if inp.strip():
            lst.append(inp)
        else:
            break
        i += 1
    print()
    return lst


def print_line(speaker, line, end="\n"):
    if isinstance(line, list):
        indent = " " * 4
        print_line(speaker, "")
        for i, l in enumerate(line):
            print(indent + l, end=end if i == len(line) - 1 else "\n")
    else:
        line = str(line)
        print(f"{profiles[speaker]}: {Style.RESET_ALL}{line}", end=end)


def prompt(speaker, line):
    print_line(speaker, line, end="")
    return input()


def write_divider(big=False, default_columns=80):
    char = "\u2501" if big else "\u2500"
    try:
        columns = os.get_terminal_size().columns
    except OSError:
        columns = default_columns
    print(char * columns)


def check_agent_config(agent):
    if agent.name is None or agent.name == DEFAULT_AGENT_NAME:
        name = prompt("loopgpt", "Enter the name of your AI agent: ")
        if name.lower().strip() == "exit":
            return -1
        if name.strip() == "":
            name = "LoopGPT"
        agent.name = name

    if agent.description is None or agent.description == DEFAULT_AGENT_DESCRIPTION:
        description = prompt("loopgpt", "Enter a description for your AI agent: ")
        if description.lower().strip() == "exit":
            return -1
        agent.description = description

    if agent.goals == []:
        goals = listed_prompt("loopgpt", "Enter the goals of your AI agent: ", "Goal")
        if goals == -1:
            return -1
        agent.goals = goals

    profiles[agent.name] = Fore.GREEN + agent.name


def cli(agent, continuous=False):
    print(HEADER)
    res = check_agent_config(agent)
    if res == -1:
        return
    write_divider(big=True)
    resp = agent.chat()
    n = 1
    while True:
        if isinstance(resp, str):
            print_line(agent.name, resp)
        else:
            if "thoughts" in resp:
                msgs = {}
                thoughts = resp["thoughts"]
                if "text" in thoughts:
                    msgs[agent.name] = thoughts["text"]
                if "reasoning" in thoughts:
                    msgs["reasoning"] = thoughts["reasoning"]
                if "plan" in thoughts:
                    msgs["plan"] = (
                        thoughts["plan"].split("\n")
                        if isinstance(thoughts["plan"], str)
                        else thoughts["plan"]
                    )
                if "progress" in thoughts:
                    msgs["progress"] = thoughts["progress"]
                if "speak" in thoughts:
                    msgs["speak"] = "(voice) " + thoughts["speak"]
                for kind, msg in msgs.items():
                    print_line(kind, msg, end="\n\n")
            if "command" in resp:
                command = resp["command"]
                if (
                    isinstance(command, dict)
                    and "name" in command
                    and "args" in command
                ):
                    if command["name"]:
                        print_line(
                            "command",
                            f"{command['name']}, Args: {command['args']}",
                            end="\n\n",
                        )
                    while True:
                        if continuous or n > 1:
                            yn = "y"
                            n -= 1
                        else:
                            inp = input(
                                f"Execute? (Y/N/Y:n to execute n steps continuously): "
                            )
                            yn, n = inp.split(":") if ":" in inp else (inp, 1)
                            n = int(n)
                            yn = yn.lower().strip()
                            if yn == "exit":
                                return
                        if yn in ("y", "n"):
                            break
                    if yn == "y":
                        cmd = agent.staging_tool.get("name", agent.staging_tool)
                        if cmd == "task_complete":
                            return
                        print_line("system", f"Executing command: {cmd}")
                        resp = agent.chat(run_tool=True)
                        print_line("system", f"{cmd} output: {agent.tool_response}")
                    elif yn == "n":
                        feedback = input(
                            "Enter feedback (Why not execute the command?): "
                        )
                        if feedback.lower().strip() == "exit":
                            return
                        resp = agent.chat(feedback, False)
                    write_divider()
                    continue
        write_divider()
        inp = input(INPUT_PROMPT)
        if inp.lower().strip() == "exit":
            return
        resp = agent.chat(inp)
