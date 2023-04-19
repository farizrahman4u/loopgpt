
<H1>
<p align="center">
  L♾️pGPT
</p>
</H1>
<p align="center">
    <b>A Modular Auto-GPT Framework</b>
</p>


L♾️pGPT is a re-implementation of the popular [Auto-GPT](https://github.com/Significant-Gravitas/Auto-GPT) project as a proper python package, written with modularity and extensibility in mind.

## 🚀 Features 🚀

1. **"Plug N Play" API** - Extensible and modular "Pythonic" framework, not just a command line tool. Easy to add new features, integrations and custom agent capabilities, all from python code, no nasty config files!
2. **GPT 3.5 friendly** - Better results than Auto-GPT for those who don't have GPT-4 access yet!
3. **Minimal prompt overhead** - Every token counts. We are continuously working on getting the best results with the least possible number of tokens.
4. **Human in the Loop** - Ability to "course correct" agents who go astray via human feedback.
5. **Full state serialization** - Pick up where you left off; L♾️pGPT can save the complete state of an agent, including memory and the states of its tools to a file or python object. No external databases or vector stores required (but they are still supported)!


## 🧑‍💻 Installation

### Install from PyPI

```bash
pip install loopgpt
```

### Install from source

```bash
pip install git+https://www.github.com/farizrahman4u/loopgpt.git@main
```

### Install from source (dev)

```bash
git clone https://www.github.com/farizrahman4u/loopgpt.git@main
cd loopgpt
python setup.py develop
```

## 🏎️ Getting Started


### Create a new L♾️pGPT Agent🕵️:

```python
from loopgpt.agent import Agent

agent = Agent()
```

L♾️pGPT uses `gpt-3.5-turbo` by default and all outputs shown here are made using it. GPT-4 users can set `model="gpt-4"` instead:

```python
agent = Agent(model="gpt-4")
```


### Setup the Agent🕵️'s attributes:

```python
agent.name = "ResearchGPT"
agent.description = "an AI assistant that researches and finds the best tech products"
agent.goals = [
    "Search for the best headphones on Google",
    "Analyze specs, prices and reviews to find the top 5 best headphones",
    "Write the list of the top 5 best headphones and their prices to a file",
    "Summarize the pros and cons of each headphone and write it to a different file called 'summary.txt'",
]
```

And we're off! Let's run the Agent🕵️'s CLI:

```python
agent.cli()
```

You can exit the CLI by typing "exit".

<img src="/docs/assets/imgs/loopgpt_demo_pic.png?raw=true" height="350">

### 🔁 Continuous Mode 🔁

If `continuous` is set to `True`, the agent will not ask for the user's permission to execute commands. Use it at your own risk
as it can go into infinite loops!

```python
agent.cli(continuous=True)
```

### 💾 Save and Load Agent State 💾

You can save the agent's state to a json file with:

```python
agent.save("ResearchGPT.json")
```

This saves the agent's configuration (model, name, description etc) as well as its internal state (conversation state, memory, tools states etc).
You can also save just the confifguration by passing `include_state=False` to `agent.save()`:

```python
agent.save("ResearchGPT.json", include_state=False)
```

You can then pick up where you left off with:

```python
import loopgpt
agent = loopgpt.Agent.load("ResearchGPT.json")
agent.cli()
```

You can also run a saved agent from the command line:

```bash
loopgpt run ResearchGPT.json
```

You can convert the agent state to a json compatible python dictionary instead of writing to a file:

```python
agent_config = agent.config()
```

To get just the configuration without the internal state:

```python
import loopgpt

agent = loopgpt.Agent.from_config(agent_config)
```


## ⚒️ Adding custom tools ⚒️

L♾️pGPT agents come with a set of builtin tools which allows them to perform variouos basic tasks such as searching the web, filesystem operations, etc. You can view these tools with `print(agent.tools)`.

In addition to these builtin tools, you can also add your own tools to the agent's toolbox.

### Example: WeatherGPT 🌦️

Let's create WeatherGPT, an AI assistant for all things weather.

A tool inherits from `BaseTool` and you only need to override 3 methods to get your tool up and running!

- `args`: A dictionary describing the tool's arguments and their descriptions.
- `resp`: A dictionary describing the tool's response and their descriptions.
- `run`: The tool's main logic. It takes the tool's arguments as input and returns the tool's response.

```python
from loopgpt.tools import BaseTool

class GetWeather(BaseTool):
    @property
    def args(self):
        return {"city": "A string with the name of the city"}
    
    @property
    def resp(self):
        return {"report": "The weather report for the city"}
    
    def run(self, city):
        ...
```

L♾️pGPT gives a default ID and description to your tool but you can override them if you'd like:

```python
class GetWeather(BaseTool):
    ...

    @property
    def id(self):
        return "get_weather_command"
    
    @property
    def desc(self):
        """A description is recommended so that the agent knows more about what the tool does"""
        return "Quickly get the weather for a given city"
```

Now let's define what our tool will do in its `run` method:

```python
import requests

# Define your custom tool
class GetWeather(BaseTool):
    ...
    
    def run(self, city):
        try:
            url = "https://wttr.in/{}?format=%l+%C+%h+%t+%w+%p+%P".format(city)
            data = requests.get(url).text.split(" ")
            keys = ("location", "condition", "humidity", "temperature", "wind", "precipitation", "pressure")
            data = {"report": dict(zip(keys, data))}
            return data
        except Exception as e:
            return f"An error occured while getting the weather: {e}."
```

That's it! You've built your first custom tool. Let's register it with a new agent and run it:

```python
import loopgpt
# Create Agent
agent = loopgpt.Agent()
agent.name = "WeatherGPT"
agent.description = "an AI assistant that tells you the weather"
agent.goals = [
    "Get the weather for NewYork and Beijing",
    "Give the user tips on how to dress for the weather in NewYork and Beijing",
    "Write the tips to a file called 'dressing_tips.txt'"
]


# Register custom tool type
# This is actually not required here, but is required when you load a saved agent with custom tools.
loopgpt.tools.register_tool_type(GetWeather)

# Register Tool
weather_tool = GetWeather()
agent.tools[weather_tool.id] = weather_tool

# Run the agent's CLI
agent.cli()
```

Let's take a look at `dressing_tips.txt` that WeatherGPT wrote for us:

dressing_tips.txt
```
- It's Clear outside with a temperature of +10°C in Beijing. Wearing a light jacket and pants is recommended.
- It's Overcast outside with a temperature of +11°C in New York. Wearing a light jacket, pants, and an umbrella is recommended.
```

## 📋 Requirements

- Python 3.8+
- [An OpenAI API Key](https://platform.openai.com/account/api-keys)
- Google Chrome

### Optional Requirements

For official google search support:
- [Google API Key](https://console.developers.google.com) (for Google Search)
    - Set environment variable `GOOGLE_API_KEY` to the API key
- [Google Custom Search Engine ID](https://cse.google.com/cse/create/new) (also for Google Search)
    - Set environment variable `CUSTOM_SEARCH_ENGINE_ID` to the CSE ID

In case these are absent, LoopGPT will fall back to using [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/)


## 💌 Contribute 

Contributions are welcome! Please open an issue or a PR if you'd like to contribute.

## 🌳 Community

Join our [Community Slack]()
