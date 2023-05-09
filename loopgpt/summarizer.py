"""
Adapted from Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
"""

from typing import *
from tqdm import tqdm
from loopgpt.models import BaseModel, OpenAIModel

import loopgpt.utils.spinner


class Summarizer:
    def __init__(self, model: Optional[BaseModel] = None):
        self._model = model

    @property
    def model(self):
        if self._model is None:
            if hasattr(self, "agent"):
                model = self.agent.model
                if type(model) == OpenAIModel:
                    if model.model == "gpt-3.5-turbo":
                        self._model = model
                    else:
                        self._model = OpenAIModel("gpt-3.5-turbo")
                else:
                    self._model = model
            else:
                self._model = OpenAIModel("gpt-3.5-turbo")
        return self._model

    def qa_chunk(self, text, query):
        prompt = f"""{text}\n\nUsing the above text, try to answer the following query: "{query}". -- if the query cannot be answered using the text, say \"NO ANSWER\"\n"""
        resp = self.model.chat(
            [{"role": "user", "content": prompt}], temperature=0, max_tokens=300
        )
        if "NO ANSWER" in resp.upper():
            return ""  # FIXME
        return resp

    def summarize_chunk(self, text, query):
        prompt = f"""Summarize the following text: \n"{text}"\n"""
        resp = self.model.chat(
            [{"role": "user", "content": prompt}], temperature=0, max_tokens=300
        )
        return resp

    def qa_or_summarize_chunk(self, text, query):
        ans = self.qa_chunk(text, query)
        if ans:
            return {
                "has_answer": True,
                "answer": ans,
            }
        else:
            resp = self.summarize_chunk(text, query)
            return {
                "has_answer": False,
                "summary": resp,
            }

    def summarize(self, text: str, query: str):
        spinner = loopgpt.utils.spinner.ACTIVE_SPINNER
        if spinner:
            spinner.hide()
        summaries = []
        for chunk in tqdm(list(self._chunk_text(text)), desc="Summarizing text..."):
            if not query:
                summary = self.summarize_chunk(chunk, query)
                summaries.append(summary)
            else:
                ans = self.qa_chunk(chunk, query)
                if ans:
                    summaries.append(ans)
        if not summaries:
            return "NOTHING FOUND", []
        summary = "\n".join(summaries)
        summary = self.summarize_chunk(summary, query)
        if spinner:
            spinner.show()
        return summary, summaries

    def _count_tokens(self, text):
        return self.model.count_tokens(
            [
                {
                    "role": "system",
                    "summary": text,
                }
            ],
        )

    def _chunk_text(self, text: str, chunk_size=900) -> List[str]:
        paras = text.split("\n")
        curr_token_count = 0
        curr_chunk = []
        for p in paras:
            new_token_count = curr_token_count + self._count_tokens(p)
            if new_token_count < chunk_size:
                curr_chunk.append(p)
                curr_token_count = new_token_count
            else:
                yield "\n".join(curr_chunk)
                curr_chunk = [p]
                curr_token_count = self._count_tokens(p)
        if curr_chunk:
            yield "\n".join(curr_chunk)

    def _prompt(self, text: str, query: str):
        return {
            "role": "user",
            "content": f'"""{text}""" Using the above text, please answer the following question: "{query}" -- if the question cannot be answered using the text, please summarize the text.',
        }
