from loopgpt.tools.base_tool import BaseTool
from loopgpt.utils.spinner import hide_spinner


class _UserManagerTool(BaseTool):
    pass


class AskUser(_UserManagerTool):
    @property
    def args(self):
        return {"message": "The question for the user."}

    @property
    def resp(self):
        return {"response": "The response from the user."}

    @property
    def desc(self):
        return "Use this command to get input from the user."

    @hide_spinner
    def run(self, message):
        return {"response": input(f"{message}: ")}
