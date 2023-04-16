import loopgpt


def cli(agent):
    resp = agent.chat()
    while True:
        if isinstance(resp, str):
            print(f"{agent.name}: {resp}")
        else:
            msgs = []
            if "text" in resp:
                msgs.append(resp["text"])
            if "reasoning" in resp:
                msgs.append(f"Reasoning: {resp['reasoning']}")
            if "plan" in resp:
                msgs += resp["plan"].split("\n")
            if "criticism" in resp:
                msgs.append(f"Criticism: {resp['criticism']}")
            if "speak" in resp:
                msgs.append(f"(voice) {resp['speak']}")
            for msg in msgs:
                print(f"{agent.name}: {msg}")
            if "command" in resp:
                print(
                    f"Agent wants to execute the following command :\n{resp['command']}"
                )
                while True:
                    yn = input(f"(Y/N)?")
                    yn = yn.lower().strip()
                    if yn in ("y", "n"):
                        break
                if yn == "y":
                    resp = agent.chat("GENERATE NEXT COMMAND JSON", True)
                elif yn == "n":
                    feedback = input("Enter feedback (Why not execute the command?): ")
                    resp = agent.chat(feedback, False)
                continue
        inp = input("Enter message: ")
        if inp.lower().strip() == "exit":
            return
        resp = agent.chat(inp)
