from typing import Dict, List, Optional, Union
from loopgpt.models.base import BaseModel
from loopgpt.models.llama_ import LLamaModel

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
    def __init__(
        self,
        model="stabilityai/stablelm-tuned-alpha-7b",
        load_in_8bit=False,
        model_max_length=1024,
    ):
        import torch

        try:
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                StoppingCriteriaList,
            )
        except ImportError as e:
            raise ImportError(
                "Please install transformers (pip install transformers) to use hugging face model."
            ) from e

        super(HuggingFaceModel, self).__init__()
        self.model_name = model
        self.load_in_8bit = load_in_8bit
        self.model_max_length = model_max_length
        self.tokenizer = AutoTokenizer.from_pretrained(
            model, model_max_length=model_max_length
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model,
            torch_dtype=torch.float16,
            load_in_8bit=load_in_8bit,
            device_map="auto",
            offload_folder="./offload",
        )
        # self.model.to(torch.device("cuda"))
        self.stopping_criteria = StoppingCriteriaList([StopOnTokens()])

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        for msg in messages:
            print(msg)
        prompt = self.encode_messages(messages)
        encoding = self.tokenizer(
            prompt, return_tensors="pt", return_token_type_ids=False
        )
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
        if self.model_name.startswith("meta-llama"):
            messages = LLamaModel._convert_to_llama_dialogs(messages)[0]
        return self.tokenizer.apply_chat_template(messages, tokenize=False)

    def count_tokens(self, messages: Union[List[Dict[str, str]], str]) -> int:
        data = self.encode_messages(messages)
        return len(self.tokenizer.encode(data))

    def get_token_limit(self):
        return self.tokenizer.model_max_length

    def config(self):
        cfg = super().config()
        cfg.update(
            {
                "model": self.model_name,
                "load_in_8bit": self.load_in_8bit,
                "model_max_length": self.model_max_length,
            }
        )
        return cfg

    @classmethod
    def from_config(cls, config):
        return cls(**config)
