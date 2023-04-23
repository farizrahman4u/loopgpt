"""
Adapted from Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
"""


from bs4 import BeautifulSoup
from loopgpt.tools.browser import Browser
from loopgpt.summarizer import Summarizer
import atexit
import requests


class SimpleBrowser(Browser):
    """Alternative browser implementation that uses requests library instead of the default Google Chrome implementation.

    Usage:

    ```
    import loopgpt
    agent = loopgpt.Agent(...)
    agent.tools["browser"] = SimpleBrowser()
    ```
    """

    def __init__(self):
        super(SimpleBrowser, self).__init__()
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
            }
        )
        self.session = session
        self.summarizer = Summarizer()
        self.cache = {}

    def _get(self, url):
        if url in self.cache:
            return self.cache[url]
        resp = self.session.get(url)
        if resp.status_code >= 400:
            return f"HTTP Error {resp.status_code}"
        self.cache[url] = resp.text
        return resp.text

    @property
    def id(self):
        return "browser"
