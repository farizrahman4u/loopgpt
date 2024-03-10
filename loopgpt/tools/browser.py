"""
Adapted from Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT)
"""

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchWindowException
from loopgpt.tools.base_tool import BaseTool
from selenium.webdriver.support import expected_conditions
from loopgpt.summarizer import Summarizer
from loopgpt.logger import logger
import logging
import atexit


class Browser(BaseTool):
    """This opens a browser. It opens the url and finds the answer for the query.
    Provide an empty query if you want to summarize the page.

    Args:
        url (str): URL to open.
        query (str): Query to search for.

    Returns:
        Dict: Relevant summary and a list of links extracted from the URL.

    """

    is_source = True

    def __init__(self, browser_type="chrome"):
        super(Browser, self).__init__()
        if browser_type not in ("chrome", "firefox"):
            browser_type = "chrome"
        self._set_browser_options(browser_type)
        self.driver = None
        self.summarizer = Summarizer()
        self.cache = {}
        self.browsed = {}
        atexit.register(self.close)

    def _set_browser_options(self, browser_type):
        self.browser_type = browser_type
        if self.browser_type == "chrome":
            from selenium.webdriver.chrome.options import Options
        elif self.browser_type == "firefox":
            from selenium.webdriver.firefox.options import Options
        options = Options()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
        )
        if self.browser_type == "chrome":
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
        elif self.browser_type == "firefox":
            options.add_argument("TRACE")
        options.headless = True
        self.options = options

    def _init_chrome_driver(self):
        try:
            self.driver = webdriver.Chrome(options=self.options)
        except Exception as e:
            logger.log(
                logging.INFO,
                f"Failed to initialize Chrome driver due to {e}. Trying Firefox...",
            )
            self._set_browser_options("firefox")
            self._init_driver()

    def _init_firefox_driver(self):
        self.driver = webdriver.Firefox(options=self.options)

    def _init_driver(self):
        self.close()
        if self.browser_type == "chrome":
            self._init_chrome_driver()
        elif self.browser_type == "firefox":
            self._init_firefox_driver()

    def _get(self, url):
        if url in self.cache:
            return self.cache[url]
        if self.driver is None:
            self._init_driver()
        num_retries = 3
        for i in range(num_retries):
            try:
                self.driver.get(url)
                break
            except NoSuchWindowException:
                self._init_driver()
                try:
                    self.driver.get(url)
                    break
                except Exception:
                    continue
            except Exception:
                continue
        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.TAG_NAME, "body"))
        )
        ret = self.driver.execute_script("return document.body.outerHTML;")
        self.cache[url] = ret
        return ret

    def _extract_links_from_soup(self, soup):
        return [(link.text, link["href"]) for link in soup.find_all("a", href=True)]

    def _extract_text_from_soup(self, soup):
        lines = (line.strip() for line in soup.get_text().splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def run(self, url: str, query: str = ""):
        if not isinstance(url, str):
            return "Scraping website failed. The URL must be a string."
        if self.browsed.get(f"{url}_{query}"):
            return self.browsed[f"{url}_{query}"]
        try:
            soup = BeautifulSoup(self._get(url), "html.parser")
            [script.extract() for script in soup(["script", "style"])]
            links = self._extract_links_from_soup(soup)[:5]
            text = self._extract_text_from_soup(soup)
            self.summarizer.agent = getattr(self, "agent")
            summary, chunks = self.summarizer.summarize(text, query)
            if getattr(self, "agent"):
                for chunk in chunks:
                    self.agent.memory.add(f"Snippet from {url}: {chunk}")

            result = (
                summary
                + "\n\n"
                + "Links found on the page:\n"
                + "\n".join([f"{link[1]}: {link[0]}" for link in links])
            )
            self.browsed[f"{url}_{query}"] = result
            return result
        except Exception as e:
            return f"An error occurred while scraping the website: {e}. Make sure the URL is valid."

    def config(self):
        config = super().config()
        config["browser_type"] = self.browser_type
        return config

    @classmethod
    def from_config(cls, config):
        return cls(config["browser_type"])
