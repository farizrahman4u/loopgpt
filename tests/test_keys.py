import builtins
import os


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
