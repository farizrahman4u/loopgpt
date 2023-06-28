from loopgpt.tools import BaseTool, WriteToFile
from loopgpt.agent import Agent

import loopgpt.tools
import requests


class GetWeather(BaseTool):
    """Quickly get the weather for a given city

    Args:
        city (str): Name of the city

    Returns:
        dict: The weather report for the city
    """

    def __init__(self):
        super(GetWeather, self).__init__()

    def run(self, city: str):
        try:
            if not isinstance(city, str):
                return "Error: The city name should be a string."
            city.replace(" ", "%20")
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
            data = dict(zip(keys, data))
            return data
        except Exception as e:
            return f"An error occurred while getting the weather: {e}."


loopgpt.tools.register_tool_type(GetWeather)

agent = Agent(tools=[GetWeather, WriteToFile])
agent.name = "WeatherGPT"
agent.description = "an AI assistant that tells you the weather"
agent.goals = [
    "Get the weather for Chicago and Beijing",
    "Give the user tips on how to dress for the weather in Chicago and Beijing and write them to a file called 'dressing_tips.txt'",
    "Terminate the session when the file is written",
]

agent.cli()
