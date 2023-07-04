from typing import List
from loopgpt.tools.base_tool import BaseTool
from loopgpt.models import BaseModel, OpenAIModel
import subprocess
import sys
import os


def ai_function(func, desc, args, model: BaseModel):
    """Credits: Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
    Also see: https://github.com/Torantulino/AI-Functions
    """
    msgs = [
        {
            "role": "system",
            "content": f"You are now the following python function: ```# {desc}\n{func}```\n\nOnly respond with your `return` value.",
        },
        {"role": "user", "content": ", ".join(map(str, args))},
    ]
    return model.chat(messages=msgs, temperature=0.0)


class _BaseCodeTool(BaseTool):
    @property
    def model(self):
        if getattr(self, "agent"):
            return self.agent.model
        return OpenAIModel("gpt-3.5-turbo")


class ExecutePythonFile(_BaseCodeTool):
    """Execute a Python file and return the output.

    Args:
        file (str): Path to the Python file.

    Returns:
        str: Value of stdout if the execution was successful. Else error message.
    """

    def run(self, file: str):
        if not os.path.isfile(file):
            return f"File {file} does not exist."
        if not file.lower().endswith(".py"):
            return f"Only files with '.py' extension are allowed."
        res = subprocess.run(
            f"{sys.executable} {file}",
            capture_output=True,
            encoding="utf-8",
            shell=True,
        )
        if res.returncode:
            return f"Error: {res.stderr}"
        else:
            return res.stdout


class ReviewCode(_BaseCodeTool):
    """Review a piece of code and return a list of suggestions to improve it.

    Args:
        code (str): Code to evaluate.

    Returns:
        List[str]: List of suggestions to improve the code.
    """

    def run(self, code: str):
        func = "def analyze_code(code: str) -> List[str]:"
        desc = (
            "Analyzes the given code and returns a list of suggestions"
            " for improvements."
        )
        return ai_function(func, desc, [code], model=self.model)


class ImproveCode(_BaseCodeTool):
    """Improve a piece of code given a list of suggestions.

    Args:
        code (str): The code to improve.
        suggestions (List[str]): List of suggestions

    Returns:
        str: Improved code.
    """

    def run(self, code: str, suggestions: List[str]):
        func = "def generate_improved_code(suggestions: str, code: str) -> str:"
        desc = "Improves the provided code based on the suggestions provided, making no other changes."
        return ai_function(func, desc, [code, str(suggestions)], model=self.model)


class WriteTests(_BaseCodeTool):
    """Write tests for a piece of code.

    Args:
        code (str): Code to write tests for.

    Returns:
        str: Tests.
    """

    def run(self, code: str):
        func = "def create_test_cases(code: str, focus: Optional[str] = None) -> str:"
        desc = "Generates test cases for the existing code, focusing on specific areas if required."
        return ai_function(func, desc, [code], model=self.model)
