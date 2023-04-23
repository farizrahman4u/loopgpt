from typing import *
from loopgpt.logger import logger
import tempfile
import subprocess

from loopgpt.models.base import BaseModel


def llama_executable() -> Optional[str]:
    import os

    if not "LLAMA_CPP" in os.environ:
        logger.warn(
            "llama.cpp executable not found. Please set the `LLAMA_CPP` "
            "environment variable to the path to the `main` executable to "
            "use the llama.cpp backend."
        )
        return None
    return os.environ["LLAMA_CPP"]


class LlamaCppModel(BaseModel):
    def __init__(self, model: Optional[str], prompt_style: str = "alpaca"):
        self.model = model
        self.prompt_style = prompt_style

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.8,
    ) -> str:
        llama_bin = llama_executable()

        if max_tokens is None:
            max_tokens = self.get_token_limit()

        msg = self.encode_messages(messages)
        with tempfile.NamedTemporaryFile(
            mode="w",
        ) as fp:
            fp.write(msg)
            fp.flush()

            arguments = [
                llama_bin,
                "--file",
                fp.name,
                "--temp",
                str(temperature),
                "-n",
                str(max_tokens),
                "-c",
                str(self.get_token_limit()),
            ]
            if self.model:
                arguments += ["--model", self.model]

            output = subprocess.check_output(arguments)
            output = output.decode("utf-8").lstrip()
            if output.startswith(msg.lstrip()):
                output = output[len(msg.lstrip()) :]
            return output

    def encode_messages(self, messages: List[Dict[str, str]]):
        message_format = {
            "alpaca": {
                "system": "{0}\n",
                "user": "### Instruction:\n{0}",
                "assistant": "### Response:\n{0}",
            },
            "vicuna": {
                "system": "{0}\n",
                "user": "### Human:\n{0}",
                "assistant": "### Assistant:\n{0}",
            },
            "openassistant": {
                "system": "{0}\n",
                "user": "<|prompter|>{0}<|endoftext|>",
                "assistant": "<|assistant|>{0}<|endoftext|>",
            },
        }[self.prompt_style]

        data = []
        for message in messages:
            data.append(message_format[message["role"]].format(message["content"]))
        data.append(message_format["assistant"].format(""))

        return "".join(data)

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        try:
            from transformers import AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "Please install transformers (pip install transformers) to use the llama.cpp backend."
            ) from e
        tokenizer = AutoTokenizer.from_pretrained("huggyllama/llama-7b")
        data = self.encode_messages(messages)
        encoding = tokenizer(data)
        return len(encoding.input_ids)

    def get_token_limit(self) -> int:
        return 2048

    def config(self):
        cfg = super().config()
        cfg.update(
            {
                "model": self.model,
                "prompt_style": self.prompt_style,
            }
        )
        return cfg

    @classmethod
    def from_config(cls, config):
        return cls(config.get("model", None), config["prompt_style"])
