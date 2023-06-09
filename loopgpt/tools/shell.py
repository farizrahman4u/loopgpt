from loopgpt.tools.base_tool import BaseTool
import subprocess


class Shell(BaseTool):
    """Execute terminal commands.

    Args:
        command (str): The command to execute.

    Returns:
        Dict[str, str]: A dict containing the STDOUT and STDERR of the command.
    """

    def run(self, command: str):
        result = subprocess.run(command, capture_output=True, shell=True)
        return {
            "stdout": result.stdout.decode("utf-8"),
            "stderr": result.stderr.decode("utf-8"),
        }
