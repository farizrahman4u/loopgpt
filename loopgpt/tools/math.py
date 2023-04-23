from loopgpt.tools import BaseTool

from simpleeval import simple_eval


class EvaluateMath(BaseTool):
    @property
    def desc(self):
        return "Use this command to evaluate math expressions."

    @property
    def args(self):
        return {"expression: str": "The expression to evaluate"}

    @property
    def resp(self):
        return {"result": "The result of the expression"}

    def run(self, expression):
        return {"result": str(simple_eval(expression))}
