from loopgpt.tools.base_tool import BaseTool
import subprocess
import sys
import os


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
