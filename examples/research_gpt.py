import loopgpt

agent = loopgpt.Agent()

agent.name = "ResearchGPT"

agent.description = "an AI assistant that researches and finds the best tech products"

agent.goals = [
    "Search for the best headphones on Google",
    "Write the list of the top 5 best headphones and their prices to a file",
    "Summarize the pros and cons of each headphone and write it to a different file called 'summary.txt'",
    "There will be no user assistance. Terminate once writing both files is complete.",
]

agent.cli()

agent.save("research_gpt.json")
