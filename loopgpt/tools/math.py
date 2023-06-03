from loopgpt.tools import BaseTool

from simpleeval import simple_eval


class EvaluateMath(BaseTool):
    """Evaluate simple math expressions.

    Args:
        expression (str): The expression to evaluate.
    
    Returns:
        str: The result of the expression.
    """

    def run(self, expression: str):
        return str(simple_eval(expression))
