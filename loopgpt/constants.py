import json

"""
Credits: Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
"""

DEFAULT_CONSTRAINTS = [
    "Your short term memory is very short, so immediately save important information to files.",
    # "If you are unsure how you previously did something or want to recall past events, thinking about similar events will help you remember.",
    "No user assistance.",
    'Exclusively use the commands listed in double quotes e.g. "command name"',
    # "DO NOT change your plan of action mid-way through a task.",
    # "Prioritize specific tools over generic tools for performing tasks.",
]

DEFAULT_RESPONSE_FORMAT_ = {
    "thoughts": {
        "text": "thought",
        "reasoning": "reasoning",
        "plan": "- short bulleted\n- list that conveys\n- long-term plan",
        "criticism": "constructive self-criticism",
        "speak": "thoughts summary to say to user",
    },
    "command": {"name": "next command in your plan", "args": {"arg name": "value"}},
}

DEFAULT_RESPONSE_FORMAT = f"You should only respond in JSON format as described below \nResponse Format: \n{json.dumps(DEFAULT_RESPONSE_FORMAT_, indent=4)}\nEnsure the response can be parsed by Python json.loads"

DEFAULT_EVALUATIONS = [
    # "Make sure that the tools you use are aligned with your plan. THIS IS VERY IMPORTANT!",
    "Continuously review and analyze your actions to ensure you are performing to the best of your abilities.",
    "Constructively self-criticize your big-picture behavior constantly.",
    "Reflect on past decisions and strategies to refine your approach.",
    "Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps.",
]

DEFAULT_EVALUATIONS = []

SEED_INPUT = (
    "Determine which next command to use, and respond using the"
    " format specified above:"
)


DEFAULT_RESOURCES = [
    "Internet access for searches and information gathering.",
    "Long Term memory management.",
    "GPT-3.5 powered Agents for delegation of simple tasks.",
]

PROCEED_INPUT_SMALL = "GENERATE NEXT COMMAND JSON."


PROCEED_INPUT = (
    "Do the following:\n"
    + "1 - Check if the goals specified above have been achieved.\n"
    + "1.1 - If goals are achieved, execute the \"task_complete\" command.\n"
    + "1.2 - If goals are not achieved, execute the next command in your plan.\n"
    + "2 - DO NOT REPEAT COMMANDS.\n"
    + "3 - Commands are expensive. Aim to complete tasks in the least number of steps.\n"
    + "4 - Refer to outputs of previous commands before executing commands."
    + "4 - Do not use commands to retireve or analyze information you already have. Use your long term memory instead.\n"
    + "5 - Execute the \"do_nothing\" command if there is no other command to execute.\n"
    + "6 - ONLY RESPOND IN THE FOLLOWING FORMAT: (MAKE SURE THAT IT CAN BE DECODED WITH PYTHON JSON.LOADS())\n"
    + json.dumps(DEFAULT_RESPONSE_FORMAT_, indent=4) + "\n"
)


SEED_INPUT = (
    "Do the following:\n"
    + "1 - Execute the next best command to achieve the goals.\n"
    + "2 - Execute the \"do_nothing\" command if there is no other command to execute.\n"
    + "3 - ONLY RESPOND IN THE FOLLOWING FORMAT: (MAKE SURE THAT IT CAN BE DECODED WITH PYTHON JSON.LOADS())\n"
    + json.dumps(DEFAULT_RESPONSE_FORMAT_, indent=4) + "\n"
)


DEFAULT_AGENT_NAME = "LoopGPT"
DEFAULT_AGENT_DESCRIPTION = "A personal assistant that responds exclusively in JSON"
DEFAULT_GOALS = [
    "Respond exclusively in JSON format",
    "Give concise and useful responses",
    "Always execute plans to completion",
]

# SPINNER
SPINNER_ENABLED = True
SPINNER_START_DELAY = 2
