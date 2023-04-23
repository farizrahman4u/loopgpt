from typing import Dict, List, Optional, Union
from loopgpt.models.base import BaseModel

try:
    from transformers import StoppingCriteria

    class StopOnTokens(StoppingCriteria):
        def __call__(self, input_ids, scores, **kwargs) -> bool:
            stop_ids = [50278, 50279, 50277, 1, 0]
            for stop_id in stop_ids:
                if input_ids[0][-1] == stop_id:
                    return True
            return False

except ImportError:
    pass


class HuggingFaceModel(BaseModel):
    def __init__(self, model="stabilityai/stablelm-tuned-alpha-7b", load_in_8bit=False):
        import torch

        try:
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                StoppingCriteria,
                StoppingCriteriaList,
            )
        except ImportError as e:
            raise ImportError(
                "Please install transformers (pip install transformers) to use hugging face model."
            ) from e

        super(HuggingFaceModel, self).__init__()
        self.model = model
        self.load_in_8bit = load_in_8bit
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModelForCausalLM.from_pretrained(
            model,
            torch_dtype=torch.float16,
            load_in_8bit=load_in_8bit,
            device_map="auto",
            offload_folder="./offload",
        )
        self.stopping_criteria = StoppingCriteriaList([StopOnTokens()])

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        prompt = self.encode_messages(messages)
        encoding = self.tokenizer(prompt, return_tensors="pt")
        encoding.to(self.model.device)

        # Sampling args
        top_k = 0
        top_p = 0.9
        do_sample = True

        tokens = self.model.generate(
            **encoding,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            do_sample=do_sample,
            pad_token_id=self.tokenizer.eos_token_id,
            stopping_criteria=self.stopping_criteria,
        )

        completion_tokens = tokens[0][encoding["input_ids"].size(1) :]
        completion = self.tokenizer.decode(completion_tokens, skip_special_tokens=True)

        return completion

    def encode_messages(self, messages: List[Dict[str, str]]) -> str:
        message_format = {
            "system": "<|SYSTEM|>{0}",
            "user": "<|USER|>{0}",
            "assistant": "<|ASSISTANT|>{0}",
        }

        data = []
        for message in messages:
            data.append(message_format[message["role"]].format(message["content"]))
        data.append(message_format["assistant"].format(""))

        return "".join(data)

    def count_tokens(self, messages: Union[List[Dict[str, str]], str]) -> int:
        data = self.encode_messages(messages)
        encoding = self.tokenizer(data)
        return len(encoding.input_ids)

    def get_token_limit(self):
        return 4096

    def config(self):
        cfg = super().config()
        cfg.update(
            {
                "model": self.model,
                "load_in_8bit": self.load_in_8bit,
            }
        )
        return cfg

    @classmethod
    def from_config(cls, config):
        return cls(config["model"], config["load_in_8_bit"])
