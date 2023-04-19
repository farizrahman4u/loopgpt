"""
Adapted from Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
"""


from bs4 import BeautifulSoup
from loopgpt.tools.base_tool import BaseTool
from loopgpt.summarizer import Summarizer
import atexit
import requests


class SimpleBrowser(BaseTool):
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
        atexit.register(self.close)

    @property
    def id(self):
        return "browser"

    @property
    def description(self):
        return "Browser"

    def _get(self, url):
        if url in self.cache:
            return self.cache[url]
        resp = self.session.get(url)
        if resp.status_code >= 400:
            return f"HTTP Error {resp.status_code}"
        self.cache[url] = resp.text
        return resp.text

    def _extract_links_from_soup(self, soup):
        return [(link.text, link["href"]) for link in soup.find_all("a", href=True)]

    def _extract_text_from_soup(self, soup):
        lines = (line.strip() for line in soup.get_text().splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)

    @property
    def desc(self):
        return "Scrape answers for a question in a given web page"

    @property
    def args(self):
        return {"url": "URL of the website to scrape as a string", "question": "The question"}

    @property
    def resp(self):
        return {
            "text": "Summary of relevant text scraped from the website",
            "links": "list of links from the website, where each item is in the form `[link_text,link_url]`",
        }

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def run(self, url: str, question: str):
        soup = BeautifulSoup(self._get(url), "html.parser")
        [script.extract() for script in soup(["script", "style"])]
        links = self._extract_links_from_soup(soup)[:5]
        text = self._extract_text_from_soup(soup)
        self.summarizer.agent = getattr(self, "agent", None)
        summary, chunks = self.summarizer.summarize(text, question)
        if getattr(self, "agent", None):
            for chunk in chunks:
                self.agent.memory.add(f"Snippet from {url}: {chunk}")
        self.agent.memory.add(summary)
        return {
            "text": summary,
            "links": links[:5],
        }
