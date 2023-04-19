import loopgpt

agent = loopgpt.Agent()

agent.name = "ResearchGPT"

agent.description = "an AI assistant that researches and finds the best tech products"

agent.goals = [
    "Search for the best headphones on Google",
    "Analyze specs, prices and reviews to find the top 5 best headphones",
    "Write the list of the top 5 best headphones and their prices to a file",
    "Summarize the pros and cons of each headphone and write it to a different file called 'summary.txt'",
]

agent.cli()

agent.save("research_gpt.json")
