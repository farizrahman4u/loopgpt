HEADER = r"""
+------------------------------------------------------------+
| ██╗░░░░░░█████╗░░█████╗░██████╗░░██████╗░██████╗░████████╗ |
| ██║░░░░░██╔══██╗██╔══██╗██╔══██╗██╔════╝░██╔══██╗╚══██╔══╝ |
| ██║░░░░░██║░░██║██║░░██║██████╔╝██║░░██╗░██████╔╝░░░██║░░░ |
| ██║░░░░░██║░░██║██║░░██║██╔═══╝░██║░░╚██╗██╔═══╝░░░░██║░░░ |
| ███████╗╚█████╔╝╚█████╔╝██║░░░░░╚██████╔╝██║░░░░░░░░██║░░░ |
| ╚══════╝░╚════╝░░╚════╝░╚═╝░░░░░░╚═════╝░╚═╝░░░░░░░░╚═╝░░░ |
+------------------------------------------------------------+
"""

from loopgpt.constants import PROCEED_INPUT, DEFAULT_AGENT_NAME, DEFAULT_AGENT_DESCRIPTION
from colorama import Fore, Style

import os

LOOP_GPT = Fore.GREEN + "LoopGPT"
REASONING = Fore.LIGHTBLUE_EX + "REASONING"
PLAN = Fore.LIGHTYELLOW_EX + "PLAN"
CRITICISM = Fore.LIGHTRED_EX + "CRITICISM"
SPEAK = Fore.LIGHTGREEN_EX + "SPEAK"
COMMAND = Fore.LIGHTMAGENTA_EX + "NEXT_COMMAND"
INPUT_PROMPT = Fore.LIGHTYELLOW_EX + "Enter message: " + Style.RESET_ALL

profiles = {
    "loopgpt": LOOP_GPT,
    "reasoning": REASONING,
    "plan": PLAN,
    "criticism": CRITICISM,
    "speak": SPEAK,
    "command": COMMAND,
}

def listed_prompt(speaker, message, item_kind):
    print_line(speaker, message)
    indent = " " * 4
    lst = []
    i = 1
    while True:
        print(indent + f"- {Fore.LIGHTBLUE_EX}{item_kind} {i} : {Style.RESET_ALL}", end="")
        inp = input()
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
        print(f"{profiles[speaker]}: {Style.RESET_ALL}{line}", end=end)

def prompt(speaker, line):
    print_line(speaker, line, end="")
    return input()

def write_divider(big=False):
    char = u'\u2501' if big else u"\u2500"
    columns = os.get_terminal_size().columns
    print(char * columns)

def check_agent_config(agent):
    if agent.name is None or agent.name == DEFAULT_AGENT_NAME:
        agent.name = prompt("loopgpt", "Enter the name of your AI agent: ")
    
    if agent.description is None or agent.description == DEFAULT_AGENT_DESCRIPTION:
        agent.description = prompt("loopgpt", "Enter a description for your AI agent: ")
    
    if agent.goals == []:
        agent.goals = listed_prompt("loopgpt", "Enter the goals of your AI agent: ", "Goal")
    
    profiles[agent.name] = Fore.GREEN + agent.name


def cli(agent):
    print(HEADER)
    check_agent_config(agent)
    write_divider(big=True)
    resp = agent.chat()
    while True:
        if isinstance(resp, str):
            print(f"{agent.name}: {resp}")
        else:
            if "thoughts" in resp:
                msgs = []
                thoughts = resp["thoughts"]
                if "text" in thoughts:
                    msgs.append(thoughts["text"])
                if "reasoning" in thoughts:
                    msgs.append(f"Reasoning: {thoughts['reasoning']}")
                if "plan" in thoughts:
                    msgs += thoughts["plan"].split("\n")
                if "criticism" in thoughts:
                    msgs.append(f"Criticism: {thoughts['criticism']}")
                if "speak" in thoughts:
                    msgs["speak"] = "(voice)" + thoughts["speak"]
                for kind, msg in msgs.items():
                    print_line(kind, msg)
            if "command" in resp:
                command = resp["command"]
                if "name" in command and "args" in command:
                    print_line("command", f"{command['name']}, Args: {command['args']}")
                    while True:
                        yn = input(f"Execute? (Y/N): ")
                        yn = yn.lower().strip()
                        if yn in ("y", "n"):
                            break
                    if yn == "y":
                        resp = agent.chat(PROCEED_INPUT, True)
                    elif yn == "n":
                        feedback = input("Enter feedback (Why not execute the command?): ")
                        resp = agent.chat(feedback, False)
                    write_divider()
                    continue
        write_divider()
        inp = input(INPUT_PROMPT)
        if inp.lower().strip() == "exit":
            return
        resp = agent.chat(inp)
