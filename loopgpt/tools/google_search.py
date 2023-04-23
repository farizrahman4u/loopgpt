from loopgpt.tools.base_tool import BaseTool

import os


class GoogleSearch(BaseTool):
    def __init__(self):
        super(GoogleSearch, self).__init__()
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx_id = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

    @property
    def args(self):
        return {"query": "The query to search for"}

    @property
    def resp(self):
        return {
            "results": "A list of results. Each result is a list of the form [title, link, description]"
        }

    def _duckduckgo_search(self, query, num_results=8):
        from duckduckgo_search import ddg

        results = []

        for result in ddg(query, max_results=num_results):
            results.append([result["title"], result["href"], result["body"]])

        self._add_to_memory(query, results)
        return {"results": results}

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

        for result in results:
            results_.append([result["title"], result["link"], result["snippet"]])

        self._add_to_memory(query, results_)

        return {"results": results_}

    def _add_to_memory(self, query, results):
        if hasattr(self, "agent"):
            entry = f"Search result for {query}:\n"
            for r in results:
                entry += f"\t{r[0]}: {r[1]}\n"
            entry += "\n"
            self.agent.memory.add(entry)

    def run(self, query, num_results=8):
        try:
            return self._google_search(query, num_results)
        except:
            return self._duckduckgo_search(query, num_results)
