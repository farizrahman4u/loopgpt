import loopgpt

from loopgpt.tools import Browser
from loopgpt.utils.add_openai_key import AddKeyPrompt


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
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    monkeypatch.setattr('builtins.input', lambda _: 'my-api-key')

    # Run the function
    AddKeyPrompt()

    # Assert that the .env file was created with the correct key value
    with open(".env") as f:
        env = dict(line.strip().split("=") for line in f if line.strip())
        assert env["OPENAI_API_KEY"] == "my-api-key"
