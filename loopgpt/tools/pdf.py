from loopgpt.tools import BaseTool
from PyPDF2 import PdfReader
from loopgpt.summarizer import Summarizer
from tqdm import tqdm


class ReadFromPDF(BaseTool):
    """Read the next page of a PDF file.

    Args:
        file (str): Path to the file to read.

    Returns:
        str: Contents of the next page.
    """

    def __init__(self):
        super().__init__()
        self.generator = None

    def run(self, file: str) -> None:
        try:
            summarizer = Summarizer()
            if not hasattr(self, "agent"):
                raise Exception("Cannot run pdf reader without an agent")
            else:
                summarizer.agent = self.agent
            reader = PdfReader(file)
            for page in tqdm(reader.pages):
                page_text = page.extract_text()
                chunks = list(summarizer._chunk_text(page_text, chunk_size=100))
                for chunk in chunks:
                    self._add_to_memory(chunk)
        except:
            raise

    def _add_to_memory(self, text):
        self.agent.memory.add(text)
