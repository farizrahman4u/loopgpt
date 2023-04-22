from loopgpt.tools import BaseTool

class _UserManagerTool(BaseTool):
    pass

class MessageUser(_UserManagerTool):
    @property
    def args(self):
        return {
            "message": "Message or prompt for the user",
            "type": "Type of message (prompt or message)"
        }
    
    @property
    def resp(self):
        return {
            "response": "Response from the user",
        }
    
    @property
    def desc(self):
        return "Talk or ask something to the user"
    
    def run(self, message, type):
        if type == "prompt":
            inp = input(message)
        else:
            print(message)
            inp = None
        return {"response": inp}
