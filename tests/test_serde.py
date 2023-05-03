import loopgpt
import builtins
import os

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

def test_add_key_prompt(monkeypatch):
    # Set up mock user input
    responses = iter(["y", "my-api-key"])
    monkeypatch.setattr(builtins, "input", lambda _: next(responses))

    from loopgpt.utils.openai_key import check_openai_key
    # Run the function
    check_openai_key()

    # Assert that the .env file was created with the correct key value
    with open(".env", "r") as f:
        assert f.read().strip() == 'OPENAI_API_KEY = "my-api-key"'
    
    os.remove(".env")
