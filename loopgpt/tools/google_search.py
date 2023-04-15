from loopgpt.tools.base_tool import BaseTool
from duckduckgo_search import ddg

import os

class GoogleSearch(BaseTool):
    def __init__(self):
        super(GoogleSearch, self).__init__()
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx_id = os.getenv("GOOGLE_CX_ID")
    
    @property
    def desc(self):
        return "Search Google for a given query"

    @property
    def args(self):
        return {"query": "The query to search for"}

    @property
    def resp(self):
        return {
            "results": "A list of results. Each result is of the form [title, link, description]"
        }
    
    def duckduckgo_search(self, query, num_results=8):
        results = []
        for result in ddg(query, max_results=num_results):
            results.append([result["title"], result["href"], result["body"]])
        return results
    
    def google_search(self, query, num_results=8):
        from googleapiclient.discovery import build

        service = build("customsearch", "v1", developerKey=self.google_api_key)
        results = service.cse().list(q=query, cx=self.google_cx_id, num=num_results).execute().get("items", [])
        results = [[result["title"], result["link"], result["snippet"]] for result in results]
        return results
    
        

    def run(self, query, num_results=8):
        key = self.google_api_key
        if key and key.strip() and key != "your-google-api-key":
            return self.google_search(query, num_results)
        else:
            return self.duckduckgo_search(query, num_results)
