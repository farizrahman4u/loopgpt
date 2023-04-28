import wolframalpha
import loopgpt
import os

from loopgpt.tools import BaseTool


class AskWolfram(BaseTool):
    def __init__(self):
        super().__init__()
        self.client = wolframalpha.Client(os.getenv("WOLFRAM_API_KEY"))

    @property
    def desc(self):
        return "Ask Wolfram Alpha a question. Wolfram Alpha is the best choice for math questions."

    @property
    def args(self):
        return {"question: str": "The question to ask as a string in natural language."}

    @property
    def resp(self):
        return {"answer: str": "The answer to the question as a string."}

    def run(self, question):
        res = self.client.query(question)
        return {"answer": next(res.results).text}


agent = loopgpt.Agent()

ask_wolfram = AskWolfram()
agent.tools[ask_wolfram.id] = ask_wolfram

agent.name = "wolframGPT"

agent.description = "an AI assistant that can use WolframAlpha. You will be required to calculate the answer to math questions and prepare reports."

agent.constraints = [
    "Do not guess the answer to a question.",
    "Ensure the answers are correct.",
]

agent.goals = [
    (
        "Calculate the integrals of the following functions in x:\n"
        + "1. sqrt(x)\n"
        + "2. 3e^x\n"
        + "3. ((1/2x) - (2/x^2) + (3/sqrt(x)))\n"
        + "4. 2e^x + (6/x) + ln 2\n"
        + "5. (x^2 + 3x - 2) / sqrt(x)\n"
        + "6. (x^3 - 2x^2)((1/x) - 5)\n"
    ),
    "Write a latex report with heading 'Example Integrals', including the author and date to a file called 'example_integrals.tex'.",
    "Terminate once the report has been created.",
]

agent.cli()
