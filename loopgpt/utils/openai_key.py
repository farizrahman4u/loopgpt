import os
import openai

from typing import Optional
from dotenv import load_dotenv


def check_openai_key():
    if "OPENAI_API_KEY" not in os.environ:
        yn = input(
            "OpenAI API key not found. Would you like to add your key to `.env` now? (y/n): "
        )
        if yn.lower() == "y":
            key = input("Please enter your OpenAI API key: ")
            with open(".env", "w") as f:
                f.write(f'OPENAI_API_KEY = "{key}"')
                print("Key added to `.env`")
            load_dotenv()
        else:
            print(
                "Please set the `OPENAI_API_KEY` environment variable or add it to `.env`. LoopGPT cannot work without it."
            )


def get_openai_key(key: Optional[str] = None):
    # API Key precedence:
    key = key or openai.api_key or os.getenv("OPENAI_API_KEY")

    if key is None:
        raise ValueError(
            f"OpenAI API Key not found. "
            "Please set the `OPENAI_API_KEY` environment variable or add it to `.env`. "
            "See https://github.com/farizrahman4u/loopgpt#setup-your-openai-api-key- for more details"
        )
    return key
