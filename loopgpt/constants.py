"""
Credits: Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
"""

DEFAULT_CONSTRAINTS = [
    "~4000 word limit for short term memory. Your short term memory is short, so immediately save important information to files.",
    "If you are unsure how you previously did something or want to recall past events, thinking about similar events will help you remember.",
    "No user assistance",
    'Exclusively use the commands listed in double quotes e.g. "command_name"',
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

DEFAULT_EVALUATIONS = [
    "Continuously review and analyze your actions to ensure you are performing to the best of your abilities.",
    "Constructively self-criticize your big-picture behavior constantly.",
    "Reflect on past decisions and strategies to refine your approach.",
    "Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps.",
]
