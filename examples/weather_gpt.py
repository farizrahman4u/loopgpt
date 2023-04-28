from loopgpt.tools import BaseTool
from loopgpt.agent import Agent

import loopgpt.tools
import requests


class GetWeather(BaseTool):
    def __init__(self):
        super(GetWeather, self).__init__()

    @property
    def desc(self):
        return "Quickly get the weather for a given city"

    @property
    def args(self):
        return {"city": "A string with the name of the city"}

    @property
    def resp(self):
        return {"report": "The weather report for the city"}

    def run(self, city):
        try:
            if not isinstance(city, str):
                return "Error: The city name should be a string."
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


agent = Agent()
agent.name = "WeatherGPT"
agent.description = "an AI assistant that tells you the weather"
agent.goals = [
    "Get the weather for NewYork and Beijing",
    "Give the user tips on how to dress for the weather in NewYork and Beijing",
    "Write the tips to a file called 'dressing_tips.txt'",
    "Terminate the session when the file is written",
]

# register tool
custom_tool = GetWeather()
agent.tools[custom_tool.id] = custom_tool
loopgpt.tools.register_tool_type(GetWeather)

agent.cli()
