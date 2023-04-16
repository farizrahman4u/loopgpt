
def cli(agent):
    resp = agent.chat()
    while True:
        if isinstance(resp, str):
            print(f"{agent.name}: {resp}")
        else:
            if "thoughts" in resp:
                msgs = []
                thoughts = resp["thoughts"]
                if "text" in thoughts:
                    msgs.append(thoughts["text"])
                if "reasoning" in thoughts:
                    msgs.append(f"Reasoning: {thoughts['reasoning']}")
                if "plan" in thoughts:
                    msgs += thoughts["plan"].split("\n")
                if "criticism" in thoughts:
                    msgs.append(f"Criticism: {thoughts['criticism']}")
                if "speak" in thoughts:
                    msgs.append(f"(voice) {thoughts['speak']}")
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
