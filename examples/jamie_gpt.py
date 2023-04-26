import loopgpt

agent = loopgpt.Agent()

agent.name = "Jamie"

agent.description = (
    "the AI podcast producer of 'The Joe Rogan Experience'. Joe has podcasts planned for this week with Elon Musk, Jordan Peterson and David Goggins."
    + "Research recent events that happened in the last week and prepare 5 topics to discuss with each of them with very long descriptions, website links and targeted "
    + "questions for the host (Joe Rogan). Write all of your findings to neatly formatted files. There should be one file for each guest. Remember to only include "
    + "news from the last week."
)

agent.goals = [
    "Research events of the past week on the internet",
    "Write a podcast outline for 3 guests on 5 topics with descriptions, references and targeted questions for the host (Joe Rogan)",
    "Terminate the session once all 3 files are completed.",
]

agent.cli()
