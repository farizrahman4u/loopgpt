from loopgpt.tools import BaseTool

import requests
import loopgpt


agent = loopgpt.Agent()


class GetWeather(BaseTool):
    def __init__(self):
        super(GetWeather, self).__init__()

    @property
    def desc(self):
        return "The best command to quickly get the weather for any city"

    @property
    def args(self):
        return {"city": "A string with the name of the city"}

    @property
    def resp(self):
        return {"report": "The weather report for the city"}

    def run(self, city):
        try:
            url = "https://wttr.in/{}?format=%l+%C+%h+%t+%w+%p+%P".format(city)
            data = requests.get(url).text.split(" ")
            keys = (
                "location",
                "condition",
                "humidity",
                "temperature",
                "wind",
                "precipitation",
                "pressure",
            )
            data = {"report": dict(zip(keys, data))}
            return data
        except Exception as e:
            return f"An error occurred while getting the weather: {e}."


agent.name = "VacationGPT"

agent.description = "an AI assistant that plans vacations."

agent.goals = [
    "Find the the best hotels in Greece",
    "Write the list of hotels to a file called 'hotels.txt'",
    "Scrape the reviews for hotels in Greece",
    "Write the reviews of the hotels to a file called 'reviews.txt'",
    "Check the weather in Greece",
    "Write clothing suggestions to a file called 'clothing.txt'",
    "Terminate the session once the files are completed.",
]

# register tool
custom_tool = GetWeather()
agent.tools[custom_tool.id] = custom_tool
loopgpt.tools.register_tool_type(GetWeather)

agent.temperature = 0

agent.cli()

agent.save("research_gpt.json")
