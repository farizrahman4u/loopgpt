"""
Adapted from Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
"""


from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchWindowException
from loopgpt.tools.base_tool import BaseTool
from selenium.webdriver.support import expected_conditions
from loopgpt.summarizer import Summarizer
import atexit


class Browser(BaseTool):
    def __init__(self):
        super(Browser, self).__init__()
        options = Options()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
        )
        # options.headless = True
        self.options = options
        self.driver = None
        self.summarizer = Summarizer()
        atexit.register(self.close)

    def _init_driver(self):
        self.close()
        self.driver = webdriver.Chrome(
            executable_path=ChromeDriverManager().install(), options=self.options
        )

    def _get(self, url):
        if self.driver is None:
            self._init_driver()
        try:
            self.driver.get(url)
        except NoSuchWindowException:
            self._init_driver()
            self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return self.driver.execute_script("return document.body.outerHTML;")

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
        return {"url": "URL of the website to scrape", "question": "The question"}

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
        summary = self.summarizer.summarize(text, question)
        self.agent.memory.add(summary)
        return {
            "text": summary,
            "links": links,
        }
