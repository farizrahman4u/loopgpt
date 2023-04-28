from loopgpt.tools.base_tool import BaseTool
import subprocess


class Shell(BaseTool):
    @property
    def desc(self):
        return "Use this command to execute any terminal commands. (Non interactive commands only)"

    @property
    def args(self):
        return {"command": "the command to execute"}

    @property
    def resp(self):
        return {
            "stdout": "The STDOUT",
            "stderr": "The STDERR",
        }

    def run(self, command):
        result = subprocess.run(command, capture_output=True, shell=True)
        return {
            "stdout": result.stdout.decode("utf-8"),
            "stderr": result.stderr.decode("utf-8"),
        }
