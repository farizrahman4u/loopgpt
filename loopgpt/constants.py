import json

"""
Credits: Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
"""

DEFAULT_CONSTRAINTS = [
    "~4000 word limit for short term memory. Your short term memory is short, so immediately save important information to files.",
    "If you are unsure how you previously did something or want to recall past events, thinking about similar events will help you remember.",
    "No user assistance",
    'Exclusively use a single command listed in double quotes e.g. "command_name"',
    # "Prioritize specific tools over generic tools for performing tasks.",
]

DEFAULT_RESPONSE_FORMAT = {
    "thoughts": {
        "text": "thought",
        "reasoning": "reasoning",
        "plan": "- short bulleted\n- list that conveys\n- long-term plan",
        "criticism": "constructive self-criticism",
        "speak": "thoughts summary to say to user",
    },
    "command": {"name": "command name", "args": {"arg name": "value"}},
}

DEFAULT_RESPONSE_FORMAT = f"You should only respond in JSON format as described below \nResponse Format: \n{json.dumps(DEFAULT_RESPONSE_FORMAT, indent=4)}\nEnsure the response can be parsed by Python json.loads"

DEFAULT_EVALUATIONS = [
    # "Make sure that the tools you use are aligned with your plan. THIS IS VERY IMPORTANT!",
    "Continuously review and analyze your actions to ensure you are performing to the best of your abilities.",
    "Constructively self-criticize your big-picture behavior constantly.",
    "Reflect on past decisions and strategies to refine your approach.",
    # "Every tool has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps.",
]

SEED_INPUT = (
    "Determine which next command to use, and respond using the"
    " format specified above:"
)
