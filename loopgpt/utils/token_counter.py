from loopgpt.logger import logger
from typing import List, Dict
import tiktoken

def count_message_tokens(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo"):
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warn("Warning: model not found. Using cl100k_base encoding.")
        enc = tiktoken.get_encoding("cl100k_base")
    
    if model == "gpt-3.5-turbo":
        tokens_per_message = 4
        tokens_per_name = -1
    elif model == "gpt-4":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError()
    
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(enc.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens
