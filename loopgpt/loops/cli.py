from loopgpt.agent import Agent

import argparse
import json

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("action", choices=["run"], help="Action to perform.")
    parser.add_argument("filename", help="Agent state JSON.")
    parser.add_argument("--readonly", help="Read only mode. Does not write agent state to disk.", action="store_true")
    parser.add_argument("--reset", help="Reset agent state before use. Name, goals and description are not affected.", action="store_true")

    args = parser.parse_args()

    filename = args.filename

    with open(filename, "r") as f:
        agent_state = json.load(f)

    agent = Agent.from_config(agent_state)

    if args.reset:
        agent.clear_state()

    agent.cli()

    if not args.readonly:
        with open(filename, "w") as f:
            json.dump(agent.config(), f)
