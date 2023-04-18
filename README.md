
<p align="center">
<img src="/logo.svg?raw=true" width=100>
</p>
<H1>
<p align="center">
  LoopGPT
</p>
</H1>
<p align="center">
    <b>A Modular Auto GPT Framework</b>
</p>


LoopGPT is a re-implementation of the popular [Auto-GPT](https://github.com/Significant-Gravitas/Auto-GPT) project as a proper python package, written with modularity and extensibility in mind.

## Table of Contents

- Installation
 - API
 - Add custom tools
 - Features
 - Requirements
 - Agents
 - Tools
 - Google API Keys Configuration
 
## Installation

```bash
pip install loopgpt
```

## API

```python
from loopgpt.agent import Agent

agent = Agent(model="gpt-3.5-turbo")
# Give the agent a name and a description
agent.name = "ResearchGPT"
agent.description = "an AI assistant that researches and finds the best tech products"
# Set the agent's goals
agent.goals = [
	"Search for the best headphones on Google",
	"Analyze specs, prices and reviews to find the top 5 best headphones",
	"Write the list of the top 5 best headphones and their prices to a file",
	"Summarize the pros and cons of each headphone and write it to a different file called 'summary.txt'",
]

# Run the agent's CLI
agent.cli(continuous=False)

# Save the agent
agent.save("ResearchGPT.json")
```

Output:

<img src="/loopgpt_demo_pic.png?raw=true">

Pick up where you left off with

```bash
loopgpt run TechGPT.json
```

or

```python
agent.load("ResearchGPT.json")
```

## Add custom tools

Easily add your own tools for use by Agents:

```python
from loopgpt.tools import BaseTool
import requests

# Define your custom tool
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
            url = "https://wttr.in/{}?format=%l+%C+%h+%t+%w+%p+%P".format(city)
            data = requests.get(url).text.split(" ")
            keys = ("location", "condition", "humidity", "temperature", "wind", "precipitation", "pressure")
            data = {"report": dict(zip(keys, data))}
            return data
        except Exception as e:
            return f"An error occured while getting the weather: {e}."

from loopgpt.agent import Agent
import loopgpt.tools

# Create Agent
agent = Agent()
agent.name = "WeatherGPT"
agent.description = "an AI assistant that tells you the weather"
agent.goals = [
    "Get the weather for NewYork and Beijing",
    "Give the user tips on how to dress for the weather in NewYork and Beijing",
    "Write the tips to a file called 'dressing_tips.txt'"
]

# Register Tool
custom_tool = GetWeather()
agent.tools[custom_tool.id] = custom_tool
loopgpt.tools.register_tool_type(GetWeather)

# Run the agent's CLI
agent.cli()
```
Output:

dressing_tips.txt
```
- It's Clear outside with a temperature of +10°C in Beijing. Wearing a light jacket and pants is recommended.
- It's Overcast outside with a temperature of +11°C in New York. Wearing a light jacket, pants, and an umbrella is recommended.
```
