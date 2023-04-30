import os

key = "OPENAI_API_KEY"
env_file = ".env"


def check_openai_key():
    if "OPENAI_API_KEY" not in os.environ:
        AddKeyPrompt(user_input=input)

class AddKeyPrompt():
    def __init__(self, user_input):
        if key not in os.environ:
            if not os.path.isfile(env_file):
                response = user_input(
                    f"Key not found in {env_file}. Would you like to add it now? (y/n) ")
                if response.lower() == "y":
                    key_value = user_input("Please enter the value for the key: ")
                    with open(env_file, "w") as f:
                        f.write(f"{key}={key_value}\n")
                        print(f"Key added to {env_file}")
                    os.environ[key] = key_value # set the environment variable here
                else:
                    print("Exiting program...")
            else:
                with open(env_file) as f:
                    env = dict(line.strip().split("=") for line in f if line.strip())
                    if key not in env:
                        response = user_input(
                            f"Key not found in {env_file}. Would you like to add it now? (y/n) ")
                        if response.lower() == "y":
                            key_value = user_input("Please enter the value for the key: ")
                            with open(env_file, "a") as f:
                                f.write(f"\n{key}={key_value}\n")
                                print(f"Key added to {env_file}")
                            os.environ[key] = key_value # set the environment variable here
                        else:
                            print("Exiting program...")
        else:
            print(f"{key} is already set to {os.environ[key]}")
