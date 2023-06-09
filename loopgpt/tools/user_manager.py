from loopgpt.tools.base_tool import BaseTool
from loopgpt.utils.spinner import hide_spinner


class _UserManagerTool(BaseTool):
    pass


class AskUser(_UserManagerTool):
    """Ask the user a question.

    Args:
        message (str): The question for the user.

    Returns:
        str: The response from the user.
    """

    @hide_spinner
    def run(self, message: str):
        return input(f"{message}: ")
