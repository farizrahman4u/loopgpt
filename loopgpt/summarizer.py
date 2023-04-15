"""
Adapted from Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
"""

from typing import *
from loopgpt.models.openai_ import chat


class Summarizer:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model

    def summarize(self, text: str, query: str):
        summaries = []
        for chunk in self._chunk_text(text):
            summaries.append(chat([self._prompt(chunk, query)], max_tokens=300))
        summary = "\n".join(summaries)
        while len(summary) > 2**13:
            summaries = []
            for chunk in self._chunk_text(summary):
                summaries.append(chat([self._prompt(chunk, query)], max_tokens=300))
            summary = "\n".join(summaries)
        return summary

    def _chunk_text(self, text: str, chunk_size=2**12) -> List[str]:
        paras = text.split("\n")
        curr_len = 0
        curr_chunk = []
        for p in paras:
            new_len = curr_len + len(p) + 1
            if new_len <= chunk_size:
                curr_chunk.append(p)
                curr_len = new_len
            else:
                yield "\n".join(curr_chunk)
                curr_chunk = [p]
                curr_len = len(p) + 1
        if curr_chunk:
            yield "\n".join(curr_chunk)

    def _prompt(self, text: str, query: str):
        return {
            "role": "user",
            "content": f'"""{text}""" Using the above text, please answer the following question: "{query}" -- if the question cannot be answered using the text, please summarize the text.',
        }
