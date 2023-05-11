from loopgpt.models import BaseModel

class DummyModel(BaseModel):
    def chat(self, messages, max_tokens=None, temperature=0.8):
        return "I am a dummy model."
    
    def count_tokens(self, messages):
        return 0
    
    def get_token_limit(self):
        return 4000
    
    def config(self):
        return {"class": self.__class__.__name__, "type": "model"}
    
    @classmethod
    def from_config(cls, config):
        return cls()
