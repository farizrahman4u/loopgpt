from loopgpt.constants import INIT_PROMPT, NEXT_PROMPT
from loopgpt.agent import Agent, AgentStates

import json

class DefaultAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompts = [INIT_PROMPT, NEXT_PROMPT]

    def _default_response_callback(self, resp):
        try:
            resp = self._load_json(resp)
            plan = resp.get("plan")
            if plan and isinstance(plan, list):
                if (
                    len(plan) == 0
                    or len(plan) == 1
                    and len(plan[0].replace("-", "")) == 0
                ):
                    self.staging_tool = {"name": "task_complete", "args": {}}
                    self.staging_response = resp
                    self.state = AgentStates.STOP
            else:
                if isinstance(resp, dict):
                    if "name" in resp:
                        resp = {"command": resp}
                    if "command" in resp:
                        self.staging_tool = resp["command"]
                        self.staging_response = resp
                        self.state = AgentStates.TOOL_STAGED
                    else:
                        self.state = AgentStates.IDLE
                else:
                    self.state = AgentStates.IDLE

            progress = resp.get("thoughts", {}).get("progress")
            if progress:
                if isinstance(plan, str):
                    self.progress += [progress]
                elif isinstance(progress, list):
                    self.progress += progress
            plan = resp.get("thoughts", {}).get("plan")
            if plan:
                if isinstance(plan, str):
                    self.plan = [plan]
                if isinstance(plan, list):
                    self.plan = plan
            return resp
        except:
            raise
    
    def _get_compressed_history(self):
        hist = self.history[:]
        system_msgs = [i for i in range(len(hist)) if hist[i]["role"] == "system"]
        assist_msgs = [i for i in range(len(hist)) if hist[i]["role"] == "assistant"]
        for i in assist_msgs:
            entry = hist[i].copy()
            try:
                respd = json.loads(entry["content"])
                thoughts = respd.get("thoughts")
                if thoughts:
                    thoughts.pop("reasoning", None)
                    thoughts.pop("speak", None)
                    thoughts.pop("text", None)
                    thoughts.pop("plan", None)
                entry["content"] = json.dumps(respd, indent=2)
                hist[i] = entry
            except:
                pass
        user_msgs = [i for i in range(len(hist)) if hist[i]["role"] == "user"]
        hist = [hist[i] for i in range(len(hist)) if i not in user_msgs]
        return hist
