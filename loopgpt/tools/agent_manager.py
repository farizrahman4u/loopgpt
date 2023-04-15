from loopgpt.tools.base_tool import BaseTool
from loopgpt.models.openai_ import chat
from typing import *
from uuid import uuid4


class _AgentMangerTool(BaseTool):
    def __init__(self, agent_map: Optional[Dict] = None):
        self.agent_map = agent_map or {}


class CreateAgent(_AgentMangerTool):
    @property
    def args(self):
        return {
            "name": "Name of the agent",
            "tool": "Specific tool for this agent",
            "prompt": "The prompt",
        }

    @property
    def resp(self):
        return {
            "id": "ID of the newly created agent.",
            "resp": "Response from the newly created agent.",
        }

    def run(self, name, tool, prompt):
        from loopgpt.agent import Agent

        agent = Agent(name=name)
        agent.tools.clear()
        agent.constraints.clear()
        id = uuid4(), hex[:8]
        self.agent_map[id] = (Agent, tool)
        resp = agent.chat(prompt)
        return {"id": id, "resp": resp}


class MessageAgent(_AgentMangerTool):
    @property
    def args(self):
        return {
            "id": "ID of the agent to send the message to",
            "message": "The message",
        }

    @property
    def resp(self):
        return {
            "resp": 'Response from the agent. If the specified agent doesn\'t exist, this field will say "AGENT NOT FOUND!".'
        }

    @property
    def run(self, id, message):
        if id not in self.agent_map:
            return {"resp": "AGENT NOT FOUND!"}
        resp = self.agent_map[id][0].chat(message)
        return {"resp": resp}


class DeleteAgent(_AgentMangerTool):
    @property
    def args(self):
        return {"id": "ID of the agent to delete"}

    @property
    def resp(self):
        return {"resp": "Whether the agent was deleted."}

    def run(self, id):
        try:
            self.agent_map.pop(id)
            return {"resp": "Deleted."}
        except KeyError:
            return {f"resp": "Specified agent (id={id} not found.)"}


class ListAgents(_AgentMangerTool):
    @property
    def args(self):
        return {}

    @property
    def resp(self):
        return {
            "agents": "List of available agents, where each item is of the for [agent id, tool]"
        }

    def run(self):
        return [[k, v[1]] for k, v in self.agent_map.items()]


AgentManagerTools = [CreateAgent, MessageAgent, DeleteAgent, ListAgents]
