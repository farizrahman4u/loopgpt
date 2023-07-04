import loopgpt
from loopgpt.tools import GoogleSearch, Browser, WriteToFile, AppendToFile

agent = loopgpt.Agent(
    tools=[GoogleSearch, Browser, WriteToFile, AppendToFile], temperature=0.2
)

agent.name = "Jamie"

agent.description = (
    "the AI podcast producer of 'The Joe Rogan Experience'. Joe has podcasts planned for this week with Elon Musk, Jordan Peterson and David Goggins."
    + "Research recent events that happened in the last week and prepare 5 topics to discuss with each of them with very long descriptions, website links and targeted "
    + "questions for the host (Joe Rogan). Write all of your findings to neatly formatted files. There should be one file for each guest. Remember to only include "
    + "news from the last week."
)

agent.goals = [
    "Research relevant events of the past week for all the guests on the internet.",
    "Write a file for each guest with 5 topics to discuss with long descriptions, website links and targeted questions for the host (Joe Rogan)."
    "Terminate the session once all 3 files are completed.",
]

agent.cli()
