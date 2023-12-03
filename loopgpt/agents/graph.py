from loopgpt.tools import GoogleSearch, Browser
from loopgpt.memory import LocalMemory
from loopgpt.agent import Agent
from itertools import repeat

import ast

class Port:
    def __init__(self, prompts):
        self.prompts = prompts
        self.history = []
        self.prompt_gen = self.next_prompt()
    
    def next_prompt(self):
        yield from self.prompts
        yield from repeat(self.prompts[-1])

class AgentNode(Agent):
    def __init__(self, name, goal, tools, prompts, model, memory):
        super().__init__(
            name,
            "a smart AI problem solver and you have to create a plan to achieve a given goal using the tools available to you.",
            tools=tools,
            prompts=prompts,
            model=model,
            memory=memory
        )
        self.parent = None
        self.tool_types = tools
        self.goal = goal
        self.ports = {
            "sub_agent_success": Port([
                "A sub agent has given the following response: ",
                "Is this response satisfactory? Strictly respond with YES or NO only.",
            ]),
            "sub_agent_failure": Port([
                "A sub agent has given a failure response: ",
                "This sub agent has been terminated, you have to create a new one. "
                + "Strictly respond with a list of dictionaries, where each dictionary has the following keys: name, goal. "
                + "The name is the name of the agent, and the goal is the goal of the agent. This will act as arguments to the create_agent tool."
                + "Your response is to be directly parsed, so do not include any other text in your response.",
            ]),
            "compiler": Port([
                "Compile your next steps into a list of dictionaries, where each dictionary has the following keys: tool, args. "
                + "The tool is the name of the tool, and the args is a dictionary of arguments to the tool. "
                + "Strictly respond with a list of dictionaries ONLY. Your response is to be directly parsed, so do not include any other text in your response.",
            ]),
            "execution": Port([
                "Respond with the next tool to run as a dictionary with the following keys: tool, args. "
                + "The tool is the name of the tool, and the args is a dictionary of arguments to the tool. "
                + "Strictly respond with a dictionary ONLY. Your response is to be directly parsed, so do not include any other text in your response."
            ])
        }
    
    def register_port(self, port_id, prompts):
        self.ports[port_id] = Port(prompts)
    
    def chat(self, message=None, port_id=None):
        if port_id:
            port = self.ports[port_id]
            orig_history = self.history
            self.history += port.history
            len_history = len(self.history)
            orig_prompt_gen = self.prompt_gen
            self.prompt_gen = port.prompt_gen
            resp = super().chat(message)
            port.history += self.history[len_history:]
            self.history = orig_history
            self.prompt_gen = orig_prompt_gen
        else:
            resp = super().chat(message)
        return resp
    
    def stopping_condition(self):
        return
    
    def get_configs(self):
        print(self.chat(self.goal))
        print(self.chat())

        while True:
            try:
                configs = self.chat()
                print(configs)
                configs = ast.literal_eval(configs)
                break
            except ValueError:
                continue
        
        return configs
    
    def create_agents(self):
        if self.parent is not None and self.stopping_condition():
            print(self.name)
            return True
        
        configs = self.get_configs()

        for config in configs:
            name, goal = config["name"], config["goal"]
            print(f"{self.name}: Creating agent {name} with goal {goal}")
            agent = self.__class__(name, goal, tools=self.tool_types, model=self.model, memory=self.memory)
            agent.parent = self
            self.sub_agents[name] = agent

class SourceNode(AgentNode):
    def __init__(self, name, goal, tools, model, memory):
        super().__init__(
            name,
            goal,
            tools,
            [
                "How would you call the tools available to you to achieve this goal: ",
                "Imagine now that you have subordinate agents, who only have access to the same tools as you do, to help you. How would you ask them to use their tools?",
                "Assume you have another tool called create_agent. Strictly respond with a list of dictionaries, where each dictionary "
                + "has the following keys: name, goal. The name is the name of the agent, and the goal is the goal of the agent. "
                + "This will act as arguments to the create_agent tool. Your response is to be directly parsed, so do not include any other text in your response."
                + "Respond with a list of dictionaries ONLY.",
            ],
            model,
            memory
        )
        self.register_port(
            "analyze",
            [
                f"Does the topic '{self.goal}' have important subtopics worth deep research or do you think researching this topic alone would be sufficient?",
                "Should we explore its subtopics or no? Strictly respond with 'yes' or 'no' only. "
                + "Your response is to be directly parsed, so do not include any other text in your response."
            ]
        )
    
    def stopping_condition(self):
        print(self.chat(port_id="analyze"))
        resp = self.chat(port_id="analyze")
        if resp.lower() == "no":
            return True
        return False


class ExecutorNode(AgentNode):
    def __init__(self, name, goal, tools, model, memory):
        super().__init__(
            name,
            goal,
            tools,
            [
                "How would you collect data and execute the tools available to you to achieve this goal: ",
                "If you were to assign each step to a sequence of subordinate agents, who only have access to the same tools as you do, what would you ask them to do?",
                "Assume you have another tool called create_agent. Strictly respond with a list of dictionaries, where each dictionary "
                + "has the following keys: name, goal. The name is the name of the agent, and the goal is the goal of the agent. "
                + "This will act as arguments to the create_agent tool. Your response is to be directly parsed, so do not include any other text in your response."
                + "Respond with a list of dictionaries ONLY."
            ],
            model,
            memory
        )
    
    def create_agents(self):
        configs = self.get_configs()

        for config in configs:
            name, goal = config["name"], config["goal"]
            print(f"{self.name}: Creating agent {name} with goal {goal}")
            agent = ExecutorNode(name, goal, tools=self.tool_types, model=self.model, memory=self.memory)
            agent.parent = self
            self.sub_agents[name] = agent
        
        return True

class AgentGraph:
    def __init__(self, root_class, goal, tools, model, embedding_provider):
        self.tools = tools
        self.model = model
        self.memory = LocalMemory(embedding_provider)
        self.root = root_class("MainAgent", goal, tools, model, self.memory)
    
    def _run(self, node):
        if node.create_agents():
            return
        for agent in node.sub_agents.values():
            self._run(agent)
    
    def run(self):
        self._run(self.root)
