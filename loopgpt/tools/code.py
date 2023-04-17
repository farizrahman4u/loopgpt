from loopgpt.tools.base_tool import BaseTool
from loopgpt.models.openai_ import chat
import subprocess
import sys
import os



def ai_function(func, desc, args, model="gpt-3.5-turbo"):
    """Credits: Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
    Also see: https://github.com/Torantulino/AI-Functions
    """
    msgs = [
        {
        "role": "system",
        "content": f"You are now the following python function: ```# {desc}\n{func}```\n\nOnly respond with your `return` value.",
        },
        {
            "role": "user",
            "content": ", ".join(map(str, args))
        }
    ]
    return chat(messages=msgs, model=model, temperature=0.)


class ExecutePythonFile(BaseTool):
    @property
    def args(self):
        return {"file": "The Python file path"}

    @property
    def resp(self):
        return {
            "output": "Value of stdout if the execution was successfull. Else error message."
        }

    def run(self, file):
        if not os.path.isfile(file):
            return {"output": f"File {file} does not exist."}
        if not file.lower().endswith(".py"):
            return {"output": f"Only files with '.py' extension allowed."}
        res = subprocess.run(
            f"{sys.executable} {file}",
            capture_output=True,
            encoding="utf-8",
            shell=True,
        )
        if res.returncode:
            return {"output": f"Error: {res.stderr}"}
        else:
            return {"output": res.stdout}


class EvaluateCode(BaseTool):
    @property
    def description(self):
        return "Returns a list of suggestions to improve a given piece of code."

    @property
    def args(self):
        return {
            "code": "Code to evaluate",
        }

    @property
    def resp(self):
        return {
            "suggestions": "List of suggestions to improve the code."
        }

    def run(self, code):
        func = "def analyze_code(code: str) -> List[str]:"
        desc = "Analyzes the given code and returns a list of suggestions" " for improvements."
        return {"suggestions": ai_function(func, desc, [code])}


class ImproveCode(BaseTool):
    @property
    def description(self):
        return "Improve a piece of code given a list of suggestions."

    @property
    def args(self):
        return {
            "code": "The code to improve.",
            "suggestions": "List of suggestions",
        }

    @property
    def resp(self):
        return {
            "improved_code": "Improved code."
        }

    def run(self, code, suggestions):
        func = "def generate_improved_code(suggestions: str, code: str) -> str:"
        desc = "Improves the provided code based on the suggestions provided, making no other changes."
        return ai_function(func, desc, [code, str(suggestions)])


class WriteTests(BaseTool):
    @property
    def args(self):
        return {
            "code": "Code to write tests for.",
        }

    @property
    def resp(self):
        return {
            "tests": "Tests."
        }

    def run(self, code):
        func = "def create_test_cases(code: str, focus: Optional[str] = None) -> str:"
        desc = "Generates test cases for the existing code, focusing on specific areas if required."
        return ai_function(func, desc, [code])
