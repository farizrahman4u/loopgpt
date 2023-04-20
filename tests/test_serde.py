import loopgpt

from loopgpt.tools import Browser


def test_serde_basic():
    agent = loopgpt.Agent()
    cfg = agent.config()
    agent2 = loopgpt.Agent.from_config(cfg)

def test_serde_browser():
    browser = Browser("firefox")
    cfg = browser.config()
    browser = Browser.from_config(cfg)
    assert browser.browser_type == "firefox"
