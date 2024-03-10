from loopgpt.models.base import BaseModel
from typing import List, Dict, Optional
import pathlib
import torch.distributed as dist
import torch.multiprocessing as mp
import os
import atexit

try:
    from llama import Llama, Dialog
    from llama.generation import E_SYS, B_SYS, B_INST, E_INST
except ImportError:
    pass


class LLamaModel(BaseModel):
    def __init__(
        self,
        ckpt_dir: str,
        tokenizer_path: str,
        max_seq_len: int = 512,
        max_batch_size: int = 8,
    ):
        os.environ["MASTER_ADDR"] = "localhost"
        os.environ["MASTER_PORT"] = "12355"
        dist.init_process_group("nccl", rank=0, world_size=1)
        self.generator = Llama.build(
            ckpt_dir=ckpt_dir,
            tokenizer_path=tokenizer_path,
            max_seq_len=max_seq_len,
            max_batch_size=max_batch_size,
        )
        self.ckpt_dir = ckpt_dir
        self.tokenizer_path = tokenizer_path
        self.max_seq_len = max_seq_len
        self.max_batch_size = max_batch_size
        atexit.register(dist.destroy_process_group, None)

    @staticmethod
    def _convert_to_llama_dialogs(messages: List[Dict[str, str]]):
        system_messages = []
        dialog = []
        for message in messages:
            (system_messages if message["role"] == "system" else dialog).append(message)

        if system_messages:
            system_message = [
                {
                    "role": "system",
                    "content": "\n\n".join(
                        [message["content"] for message in system_messages]
                    )
                    + "\n",
                }
            ]
        else:
            system_message = []

        if dialog and dialog[0]["role"] != "user":
            dialog.insert(0, {"role": "user", "content": ""})

        dialogs: List[Dialog] = [system_message + dialog]
        return dialogs

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.8,
        top_p: float = 0.9,
    ):
        dialogs = self._convert_to_llama_dialogs(messages)
        results = self.generator.chat_completion(
            dialogs,
            max_gen_len=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )[0]["generation"]["content"]
        return results

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        tokens_per_message = 1
        tokens_per_last_message = 2
        additional_tokens_per_system_message = 1
        num_tokens = 0
        n = len(messages)
        for i, message in enumerate(messages):
            if i == n - 1:
                num_tokens += tokens_per_last_message
                num_tokens += len(
                    self.generator.tokenizer.encode(
                        message["content"], bos=True, eos=False
                    )
                )
            else:
                num_tokens += tokens_per_message
                num_tokens += len(
                    self.generator.tokenizer.encode(
                        message["content"], bos=True, eos=True
                    )
                )
            if message["role"] == "system":
                num_tokens += additional_tokens_per_system_message
        return num_tokens

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        dialogs = self._convert_to_llama_dialogs(messages)
        num_tokens = 0
        for dialog in dialogs:
            if dialog[0]["role"] == "system":
                if len(dialog) > 1:
                    dialog = [
                        {
                            "role": dialog[1]["role"],
                            "content": B_SYS
                            + dialog[0]["content"]
                            + E_SYS
                            + dialog[1]["content"],
                        }
                    ] + dialog[2:]
                else:
                    dialog = [
                        {
                            "role": dialog[0]["role"],
                            "content": B_SYS + dialog[0]["content"] + E_SYS,
                        }
                    ]

            dialog_tokens: List[int] = sum(
                [
                    self.generator.tokenizer.encode(
                        f"{B_INST} {(prompt['content']).strip()} {E_INST} {(answer['content']).strip()} ",
                        bos=True,
                        eos=True,
                    )
                    for prompt, answer in zip(
                        dialog[::2],
                        dialog[1::2],
                    )
                ],
                [],
            )

            dialog_tokens += self.generator.tokenizer.encode(
                f"{B_INST} {(dialog[-1]['content']).strip()} {E_INST}",
                bos=True,
                eos=False,
            )
            num_tokens += len(dialog_tokens)
        return num_tokens

    def get_token_limit(self):
        return self.max_seq_len or 4096

    def config(self):
        cfg = super().config()
        cfg.update(
            {
                "ckpt_dir": pathlib.Path(self.ckpt_dir),
                "tokenizer_path": pathlib.Path(self.tokenizer_path),
                "max_seq_len": self.max_seq_len,
                "max_batch_size": self.max_batch_size,
            }
        )
        return cfg

    @classmethod
    def from_config(cls, config):
        config["ckpt_dir"] = str(config["ckpt_dir"])
        config["tokenizer_path"] = str(config["tokenizer_path"])
        return cls(**config)
