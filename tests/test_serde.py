import loopgpt

from loopgpt.tools import Browser
from dummy_model import DummyModel
from dummy_embedding_provider import DummyEmbeddingProvider


def test_serde_basic():
    agent = loopgpt.Agent()
    cfg = agent.config()
    agent2 = loopgpt.Agent.from_config(cfg)


def test_serde_browser():
    browser = Browser("firefox")
    cfg = browser.config()
    browser = Browser.from_config(cfg)
    assert browser.browser_type == "firefox"

def test_serde_agent_basic():
    loopgpt.models.user_providers["DummyModel"] = DummyModel
    loopgpt.embeddings.user_providers["DummyEmbeddingProvider"] = DummyEmbeddingProvider

    model = DummyModel()
    emb = DummyEmbeddingProvider()
    agent = loopgpt.Agent(model=model, embedding_provider=emb)
    agent.name = "GoodAgent"
    agent.description = "This is a good agent."
    agent.goals = ["To be a good agent.", "To be a nice agent."]
    agent.constraints = ["Only be good.", "Only be nice."]
    agent.plan = ["I will be good.", "I will be nice."]
    agent.progress = ["I am being good.", "I am being nice."]

    cfg = agent.config()
    agent2 = loopgpt.Agent.from_config(cfg)

    assert agent2.state == agent.state
    assert agent2.name == "GoodAgent"
    assert agent2.description == "This is a good agent."
    assert agent2.goals == ["To be a good agent.", "To be a nice agent."]
    assert agent2.constraints == ["Only be good.", "Only be nice."]
    assert agent2.plan == ["I will be good.", "I will be nice."]
    assert agent2.progress == ["I am being good.", "I am being nice."]

    empty_agent = loopgpt.Agent(model=model, embedding_provider=emb)
    agent.clear_state()
    cfg = agent.config()
    agent2 = loopgpt.Agent.from_config(cfg)

    assert agent2.state == empty_agent.state
    assert agent2.plan == empty_agent.plan
    assert agent2.progress == empty_agent.progress

