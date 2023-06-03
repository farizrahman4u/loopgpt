from loopgpt.tools.base_tool import BaseTool

import os


class GoogleSearch(BaseTool):
    """This tool searches google for the given query and returns the results.

    Args:
        query (str): The query to search for.
    
    Returns:
        str: Search results.
    """
    def __init__(self):
        super(GoogleSearch, self).__init__()
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx_id = os.getenv("GOOGLE_CX_ID")

    def _duckduckgo_search(self, query, num_results=8):
        from duckduckgo_search import ddg

        results = ddg(query, max_results=num_results)
        
        results_ = []
        links_and_titles_ = []

        for i, result in enumerate(results):
            links_and_titles_.append(f"{i + 1}. {result['href']}: {result['title']}")
            results_.append(f"{i + 1}. {result['href']}: {result['title']}\n{result['body']}\n")
        
        links_and_titles = "\n".join(links_and_titles_)
        results = "\n".join(results_)

        return results

    def _google_search(self, query, num_results=8):
        from googleapiclient.discovery import build

        service = build("customsearch", "v1", developerKey=self.google_api_key)
        results = (
            service.cse()
            .list(q=query, cx=self.google_cx_id, num=num_results)
            .execute()
            .get("items", [])
        )

        results_ = []
        links_and_titles_ = []
        
        for i, result in enumerate(results):
            links_and_titles_.append(f"{i + 1}. {result['link']}: {result['title']}")
            results_.append(f"{i + 1}. {result['link']}: {result['title']}\n{result['snippet']}\n")

        links_and_titles = "\n".join(links_and_titles_)
        results = "\n".join(results_)
        assert len(results) > 0, "No results found."

        return results

    def _add_to_memory(self, results):
        if hasattr(self, "agent"):
            self.agent.memory.add(results)

    def run(self, query: str):
        # try:
        results = self._google_search(query, 8)
        # except:
        #     results = self._duckduckgo_search(query, 8)
        
        if len(results) > 0:
            self._add_to_memory(results)
        else:
            results = "No results found."
        return results
