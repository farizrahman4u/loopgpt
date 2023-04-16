from loopgpt.tools.base_tool import BaseTool


class _MemoryManagerTool(BaseTool):
    pass


class AddToMemory(_MemoryManagerTool):
    @property
    def args(self):
        return {"text": "Text to be added to memory."}

    @property
    def resp(self):
        return {"success": "true or false"}

    def run(self, text):
        self.agent.memory.add(text)


MemoryManagerTools = [AddToMemory]
