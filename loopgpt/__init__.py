__version__ = "0.0.13"


from loopgpt.agent import Agent
from loopgpt.tools import *
from loopgpt.memory import *
from loopgpt.embeddings import *

agent_from_config = Agent.from_config
from loopgpt.tools import from_config as tool_from_config
from loopgpt.memory import from_config as memory_from_config
from loopgpt.embeddings import from_config as embedding_provider_from_config

from dotenv import load_dotenv
from loopgpt.utils.add_openai_key import AddKeyPrompt

import os


load_dotenv()


def check_openai_key():
    if "OPENAI_API_KEY" not in os.environ:
        AddKeyPrompt()

def from_config(config):
    return globals()[config["type"] + "_from_config"](config)


check_openai_key()
