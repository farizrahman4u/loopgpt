__version__ = "0.0.7"


from loopgpt.agent import Agent
from loopgpt.tools import *
from loopgpt.memory import *
from loopgpt.embeddings import *

agent_from_config = Agent.from_config
from loopgpt.tools import from_config as tool_from_config
from loopgpt.memory import from_config as memory_from_config
from loopgpt.embeddings import from_config as embedding_provider_from_config

from loopgpt.logger import logger
from colorama import Fore, Style

import os


def check_openai_key():
    if "OPENAI_API_KEY" not in os.environ:
        logger.warn(
            f"{Fore.RED}WARNING: OpenAI API Key not found. Please set the `OPENAI_API_KEY` environment variable. "
            f"LoopGPT cannot work without it. "
            f"See https://github.com/farizrahman4u/loopgpt#-requirements for more details{Style.RESET_ALL}"
        )


def from_config(config):
    return globals()[config["type"] + "_from_config"](config)


check_openai_key()
