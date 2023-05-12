from loopgpt.tools import BaseTool

from simpleeval import simple_eval


class EvaluateArithmetic(BaseTool):
    @property
    def desc(self):
        return "Use this command to evaluate arithmetic expressions."

    @property
    def args(self):
        return {"expression: str": "The expression to evaluate"}

    @property
    def resp(self):
        return {"result": "The result of the expression"}

    def run(self, expression):
        return {"result": str(simple_eval(expression))}


from sympy import sympify, solve, Eq
from sympy.parsing.sympy_parser import parse_expr
from sympy.parsing.sympy_parser import (
    standard_transformations,
    implicit_multiplication_application,
)


class EvaluateAlgebra(BaseTool):
    def __init__(self):
        super(EvaluateAlgebra, self).__init__()

    @property
    def desc(self):
        return (
            "Quickly solves one or more algebraic equations relative to each variable."
        )

    @property
    def args(self):
        return {"equations": "One or a comma-separated list of algebraic equations."}

    @property
    def resp(self):
        return {"results": "The values of each variable."}

    def run(self, equations):
        try:
            # if not isinstance(equations, str) and not isinstance(equations, list):
            #     return "Error: The equations should be in a string format."
            # Calculate stuff

            transformations = standard_transformations + (
                implicit_multiplication_application,
            )
            eqs = []
            if isinstance(equations, str):
                equations = equations.replace("[", "").replace("]", "").split(",")
            elif isinstance(equations, list):
                equations = equations
            else:
                raise IllegalArgumentException(
                    "Equations must be in string or list format."
                )
            for eq in equations:
                neweq = eq.replace("^", "**")
                iseq = "=" in eq
                neweq = neweq.split("=") if "=" in neweq else neweq
                # print("current equation:", neweq)
                neweq = (
                    Eq(
                        parse_expr(neweq[0], transformations=transformations),
                        parse_expr(neweq[1], transformations=transformations),
                    )
                    if "=" in eq
                    else parse_expr(neweq, transformations=transformations)
                )
                eqs.append(neweq)
            # sympy_eq = sympify(neweq)
            # sympy_eq = neweq
            sympy_eq = eqs
            # print(str(sympy_eq))
            syms = [e.free_symbols for e in sympy_eq]
            symlist = set()
            for s in syms:
                symlist = symlist | s
            if len(sympy_eq) == 1:
                outputs = [solve(sympy_eq, sym, dict=True) for sym in symlist]
                for z0 in symlist:
                    if z0 in globals():
                        del globals()[z0]
                result = {}
                # print("getting outputs from ", outputs)
                for v in outputs:
                    result = v[0] | result
            else:
                outputs = solve(sympy_eq, dict=True)
                result = outputs[0] if len(outputs) > 0 else {}

            data = {"results": str(result)}
            return data
        except Exception as e:
            return f"An error occurred while calculating the results: {e}."
