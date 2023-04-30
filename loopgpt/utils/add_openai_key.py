import os

key = "OPENAI_API_KEY"
env_file = ".env"


class AddKeyPrompt():
    def __init__(self, user_input):
        self.user_input = user_input

    def run(self):
        if key not in os.environ:
            if not os.path.isfile(env_file):
                response = self.user_input(
                    f"Key not found in {env_file}. Would you like to add it now? (y/n) ")
                if response.lower() == "y":
                    key_value = self.user_input(
                        "Please enter the value for the key: ")
                    with open(env_file, "w") as f:
                        f.write(f"{key}={key_value}\n")
                        print(f"Key added to {env_file}")
                else:
                    print("Exiting program...")
            else:
                with open(env_file) as f:
                    env = dict(line.strip().split("=")
                               for line in f if line.strip())
                    if key not in env:
                        response = self.user_input(
                            f"Key not found in {env_file}. Would you like to add it now? (y/n) ")
                        if response.lower() == "y":
                            key_value = self.user_input(
                                "Please enter the value for the key: ")
                            with open(env_file, "a") as f:
                                f.write(f"\n{key}={key_value}\n")
                                print(f"Key added to {env_file}")
                        else:
                            print("Exiting program...")
        else:
            print(f"{key} is already set to {os.environ[key]}")
