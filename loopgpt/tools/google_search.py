from loopgpt.tools.base_tool import BaseTool
from itertools import islice

import os


class GoogleSearch(BaseTool):
    """This tool searches google for the given query and returns the results.

    Args:
        query (str): The query to search for.

    Returns:
        str: Search results.
    """

    def __init__(self, num_results=8, start_page=1):
        super(GoogleSearch, self).__init__()
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx_id = os.getenv("GOOGLE_CX_ID")
        self.num = num_results
        self.start = num_results * (start_page - 1) + 1

    def _duckduckgo_search(self, query):
        from duckduckgo_search import DDGS

        results_ = []
        links_and_titles_ = []
        links = []

        with DDGS() as ddgs:
            results = islice(
                ddgs.text(query), self.start - 1, self.start + self.num - 1
            )
            for i, result in enumerate(results):
                links_and_titles_.append(
                    f"{i + 1}. {result['href']}: {result['title']}"
                )
                results_.append(
                    f"{i + 1}. {result['href']}: {result['title']}\n{result['body']}\n"
                )
                links.append(result["href"])

        links_and_titles = "\n".join(links_and_titles_)
        results = "\n".join(results_)

        return results, links

    def _google_search(self, query):
        from googleapiclient.discovery import build

        service = build("customsearch", "v1", developerKey=self.google_api_key)
        results = (
            service.cse()
            .list(q=query, cx=self.google_cx_id, num=self.num, start=self.start)
            .execute()
            .get("items", [])
        )

        results_ = []
        links_and_titles_ = []
        links = []

        for i, result in enumerate(results):
            try:
                links_and_titles_.append(
                    f"{i + 1}. {result['link']}: {result['title']}"
                )
                results_.append(
                    f"{i + 1}. {result['link']}: {result['title']}\n{result['snippet'].strip('...')}\n"
                )
                links.append(result["link"])
            except:
                continue

        links_and_titles = "\n".join(links_and_titles_)
        results = "\n".join(results_)

        return results, links

    def _add_to_memory(self, results):
        if getattr(self, "agent"):
            self.agent.memory.add(results)

    def run(self, query: str):
        try:
            results, links = self._google_search(query)
        except Exception as e:
            print(f"Google search failed with error: {e}")
            print("Trying DuckDuckGo search instead...")
            results, links = self._duckduckgo_search(query)

        assert len(results) > 0, "No results found."
        if len(results) > 0:
            self._add_to_memory(results)
        else:
            results = "No results found."
        return results, links
