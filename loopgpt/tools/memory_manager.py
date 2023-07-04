from loopgpt.tools.base_tool import BaseTool


class _MemoryManagerTool(BaseTool):
    pass


class AddToMemory(_MemoryManagerTool):
    """Add text to memory for later use.

    Args:
        text (str): Text to be added to memory.

    Returns:
        bool: True if the text was successfully added to memory. Else False.
    """

    def run(self, text: str):
        self.agent.memory.add(text)
        return True


MemoryManagerTools = [AddToMemory]
