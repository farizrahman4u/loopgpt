from loopgpt.tools.base_tool import BaseTool
from typing import *
from uuid import uuid4


class _AgentManagerTool(BaseTool):
    pass


class CreateAgent(_AgentManagerTool):
    """Create a new agent.

    Args:
        name (str): Agent name.
        task (str): Specific task for agent.
        prompt (str): The prompt.

    Returns:
        dict: A dict containing the id and response from the agent.
    """

    def run(self, name: str = "", task: str = "", prompt: str = ""):
        from loopgpt.agent import Agent

        model = self.agent.model
        emb = self.agent.embedding_provider
        agent = Agent(
            name=name,
            description=f"An agent for performing this specific task: {task}",
            model=model,
            embedding_provider=emb,
        )
        agent.tools.extend(self.agent.tools)
        id = uuid4().hex[:8]
        self.agent.sub_agents[id] = (agent, task)
        resp = agent.chat(prompt)
        return {"uuid": id, "resp": resp}


class MessageAgent(_AgentManagerTool):
    """Send a message to an agent.

    Args:
        id (str): Agent id.
        message (str): The message to send to the agent.

    Returns:
        str: The response from the agent.
    """

    def run(self, id: str, message: str):
        if id not in self.agent.sub_agents:
            return {"resp": "AGENT NOT FOUND!"}
        resp = self.agent.sub_agents[id][0].chat(message)
        return resp


class DeleteAgent(_AgentManagerTool):
    """Delete an agent.

    Args:
        id (str): Agent id.

    Returns:
        bool: True if the agent was deleted, False otherwise.
    """

    def run(self, id: str):
        try:
            self.agent.sub_agents.pop(id)
            return True
        except KeyError:
            return f"Error: Specified agent {id} not found."


class ListAgents(_AgentManagerTool):
    """List all available agents.

    Returns:
        List: List of available agents, where each item is of the form [agent_id, task]
    """

    def run(self):
        return [[k, v[1]] for k, v in self.agent.sub_agents.items()]


AgentManagerTools = [CreateAgent, MessageAgent, DeleteAgent, ListAgents]
