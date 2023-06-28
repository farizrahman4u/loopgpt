"""LoopGPT is a modular Auto-GPT framework
"""

__version__ = "0.0.16"


from loopgpt.agent import Agent
from loopgpt.tools import *
from loopgpt.memory import *
from loopgpt.embeddings import *
from loopgpt.aifunc import aifunc

agent_from_config = Agent.from_config
from loopgpt.tools import from_config as tool_from_config
from loopgpt.memory import from_config as memory_from_config
from loopgpt.embeddings import from_config as embedding_provider_from_config

from loopgpt.utils.openai_key import check_openai_key
from dotenv import load_dotenv

import sys


load_dotenv()


def from_config(config):
    return globals()[config["type"] + "_from_config"](config)


def set_aifunc_args(model, embedding_provider, memory=None):
    aifunc.model = model
    aifunc.embedding_provider = embedding_provider
    aifunc.memory = memory


if "pytest" not in sys.modules:
    check_openai_key()
