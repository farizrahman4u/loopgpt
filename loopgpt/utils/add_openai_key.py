from loopgpt.logger import logger
from colorama import Fore, Style
import os

key = "OPENAI_API_KEY"
env_file = ".env"


class AddKeyPrompt():
  if not os.path.isfile(env_file):
    logger.warn(
        f"{Fore.RED}WARNING: OpenAI API Key not found in the current working directory: {os.getcwd()}. "
        "Please set the `OPENAI_API_KEY` environment variable. "
        f"LoopGPT cannot work without it. "
        f"See https://github.com/farizrahman4u/loopgpt#-requirements for more details{Style.RESET_ALL}"
        ""
    )
    response = input(
        f"{env_file} not found in the current working directory: {os.getcwd()}. Would you like to create it and add the key now? (y/n) ")
    if response.lower() == "y":
      key_value = input("Please enter the value of the key: ")
      with open(env_file, "w") as f:
        f.write(f"{key}={key_value}\n")
        print(f"Key added to {env_file}")
    else:
      print("Exiting program...")
  else:
    with open(env_file, "r+") as f:
      env_lines = f.readlines()
      key_exists = False
      for i, line in enumerate(env_lines):
        if line.startswith(key):
          key_exists = True
          break

      if key_exists:
        print(f"Key already exists in {env_file}")
      else:
        response = input(
            f"Key not found in {env_file}. Would you like to add it now? (y/n) ")
        if response.lower() == "y":
          f.write(f"\n{key}=\n")
          print(f"Key added to {env_file}")
        else:
          print("Exiting program...")
