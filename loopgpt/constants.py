import json

"""
Credits: Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
"""


DEFAULT_RESPONSE_FORMAT_ = {
    "thoughts": {
        "text": "A short description of your next step",
        "reasoning": "The reasoning behind your next step",
        "progress": "- A detailed list\n - of everything you have done so far",
        "plan": "- short bulleted\n- list that conveys\n- long-term plan",
        "speak": "thoughts summary to say to user",
    },
    "command": {"name": "next command in your plan", "args": {"arg name": "value"}},
}


DEFAULT_RESPONSE_FORMAT = f"You should only respond in JSON format as described below \nResponse Format: \n{json.dumps(DEFAULT_RESPONSE_FORMAT_, indent=4)}\nEnsure the response can be parsed by Python json.loads"


NEXT_PROMPT_SMALL = "Next"


NEXT_PROMPT = (
    "INSTRUCTIONS:\n"
    + "1 - Check the progress of your goals.\n"
    + '2 - If you have achieved all your goals, execute the "task_complete" command IMMEDIATELY. Otherwise,\n'
    + "3 - Use the command responses in previous system messages to plan your next command to work towards your goals\n"
    + "4 - Only use available commmands.\n"
    + "5 - Commands are expensive. Aim to complete tasks in the least number of steps.\n"
    + "6 - A command is considered executed only if it is confirmed by a system message.\n"
    + "7 - A command is not considered executed just becauses it was in your plan.\n"
    + "8 - Remember to use the output of previous command. If it contains useful information, save it to a file.\n"
    + "9 - Do not use commands to retrieve or analyze information you already have. Use your long term memory instead.\n"
    + '10 - Execute the "do_nothing" command ONLY if there is no other command to execute.\n'
    + "11 - Make sure to execute commands only with supported arguments.\n"
    + "12 - ONLY RESPOND IN THE FOLLOWING FORMAT: (MAKE SURE THAT IT CAN BE DECODED WITH PYTHON JSON.LOADS())\n"
    + json.dumps(DEFAULT_RESPONSE_FORMAT_, indent=4)
    + "\n"
)

NEXT_PROMPT = (
    "INSTRUCTIONS:\n"
    + "1 - Only use available commands.\n"
    + "2 - Plan and execute commands with supported arguments to achieve your goals.\n"
    + "2 - If you have achieved all of your goals, execute the 'task_complete' command.\n"
    + f"3 - {DEFAULT_RESPONSE_FORMAT}\n"
)


INIT_PROMPT = (
    "Do the following:\n"
    + "1 - Execute the next best command to achieve the goals.\n"
    + '2 - Execute the "do_nothing" command if there is no other command to execute.\n'
    + "3 - ONLY RESPOND IN THE FOLLOWING FORMAT: (MAKE SURE THAT IT CAN BE DECODED WITH PYTHON JSON.LOADS())\n"
    + json.dumps(DEFAULT_RESPONSE_FORMAT_, indent=4)
    + "\n"
)

DEFAULT_PROMPT_TEMPLATE = """
    <HEADER>
    <HISTORY>
    <MEMORY: 10>
    <USER_INPUT>
    """


DEFAULT_AGENT_NAME = "LoopGPT"
DEFAULT_AGENT_DESCRIPTION = "A personal assistant that responds exclusively in JSON"
DEFAULT_GOALS = [
    "Respond exclusively in JSON format",
    "Give concise and useful responses",
    "Always execute plans to completion",
]


class AgentStates:
    START = "START"
    IDLE = "IDLE"
    TOOL_STAGED = "TOOL_STAGED"
    STOP = "STOP"


# SPINNER
SPINNER_ENABLED = True
SPINNER_START_DELAY = 2
