import loopgpt


def test_serde_basic():
    agent = loopgpt.Agent()
    cfg = agent.config()
    agent2 = loopgpt.Agent.from_config(cfg)
