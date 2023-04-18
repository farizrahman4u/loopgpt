import json
import inspect


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
        "plan": "- short bulleted\n- list that conveys\n- long-term plan\n including commands to execute",
        "criticism": "constructive self-criticism",
        "speak": "thoughts summary to say to user",
    },
    "command": {"name": "next command in your plan", "args": {"arg name": "value"}},
}

DEFAULT_RESPONSE_FORMAT = f"You should only respond in JSON format as described below \nResponse Format: \n{json.dumps(DEFAULT_RESPONSE_FORMAT_, indent=4)}\nEnsure the response can be parsed by Python json.loads"


DEFAULT_RESOURCES = [
    "Internet access for searches and information gathering.",
    "Long Term memory management.",
    "GPT-3.5 powered Agents for delegation of simple tasks.",
]

PROCEED_INPUT_SMALL = "GENERATE NEXT COMMAND JSON."


def generate_next_command_json() -> str:
    """Function to generate the next response json.
    The function returns a JSON string  in the specified format that can be decoded using Python's json.loads()
    Assume the values for any uknown variables based on the conversation messages.
    """
    RESPONSE_FORMAT = {
    "thoughts": {
        "text": "thought",
        "reasoning": "reasoning",
        "plan": "- short bulleted\n- list that conveys\n- long-term plan\n including commands to execute",
        "criticism": "constructive self-criticism",
        "speak": "thoughts summary to say to user",
    },
    "command": {"name": "next command in plan", "args": {"arg name": "value"}},
    }
    if last_command_executed_successfully:
        if is_empty(curent_plan):
            json_resp['command'] = {'name': 'task_complete', 'args': {}}
            points += 1000
        elif no_commands_necessary:
            json_rsp['command'] = {'name': 'do_nothing'}
            points -= 1
            cost += 10
        else:
            json_resp['command'] = {'name': 'next_command_in_plan', 'args': '<arguments dictionary>'}
            points += 1
            cost += 1
    else:
        points -= 1
    if is_subset(current_plan, original_plan):
        points += 100
    else:
        cost += 100
    fill_response(RESPONSE_FORMAT, json_resp)
    return json.dumps(RESPONSE_FORMAT)


PROCEED_INPUT = (
    "Decide your next response with the help of the following pseudo-code:\n"
    + "```psuedo-code"
    + inspect.getsource(generate_next_command_json)
    +"```"
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
