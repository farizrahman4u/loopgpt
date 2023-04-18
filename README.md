
<H1>
<p align="center">
  L⭕⭕PGPT
</p>
</H1>
<p align="center">
    <b>A Modular Auto-GPT Framework</b>
</p>


LoopGPT is a re-implementation of the popular [Auto-GPT](https://github.com/Significant-Gravitas/Auto-GPT) project as a proper python package, written with modularity and extensibility in mind.

## Table of Contents

- [Installation](#installation)
- [API] (#API)
- [Add custom tools](#add-custom-tools)
- [Features](#features)
- [Requirements](#requirements)
- Agents
- Tools
- Google API Keys Configuration
 
## Installation

```bash
pip install loopgpt
```

## API

Create a new LoopGPT agent:

    ```python
    from loopgpt.agent import Agent

    agent = Agent(model="gpt-3.5-turbo")
    ```

LoopGPT uses `gpt-3.5-turbo` by default and all outputs shown were made using it. GPT-4 users can set `model="gpt-4"` instead.

Setup the agent's attributes, this can also be done via the CLI:

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

And we're off! Let's run the agent's CLI:

    ```python
    agent.cli(continuous=False)
    ```

If `continuous` is set to `True`, the agent will not ask for the user's permission to execute commands. Use it at your own risk
since it can go into infinite loops!

You can also save the agent:

    ```python
    agent.save("ResearchGPT.json")
    ```

and pick up where you left off with:

    ```python
    agent.load("ResearchGPT.json")
    ```
or the CLI command:
    
    ```bash
    loopgpt run ResearchGPT.json
    ```

Output:

<img src="/docs/assets/imgs/loopgpt_demo_pic.png?raw=true">

## Features 🚀

1. Extensible and modular "Pythonic" library. Easy to add new features, integrations and agent capabilities via the "plug n play" API
2. GPT 3.5 friendly - Better results than Auto-GPT for those who don't have GPT-4 access yet!
3. Minimal prompt overhead - We are continuously working on getting the best results with the least possible number of tokens.
4. Ability to "course correct" agents who go astray via human feedback.

## Add custom tools

With LoopGPT, you can easily add your own tools to the agent's toolbox.

Let's create WeatherGPT, an AI assistant for all things weather.

A tool inherits from `BaseTool` and you only need to override 3 methods to get your tool up and running!

- `args`: A dictionary of the tool's arguments and their descriptions.
- `resp`: A dictionary of the tool's response and their descriptions.
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

LoopGPT gives a default ID and description to your tool but you can override them if you'd like:

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

Let's take a look at `dressing_tips.txt` that WeatherGPT wrote for us:

dressing_tips.txt
    ```
    - It's Clear outside with a temperature of +10°C in Beijing. Wearing a light jacket and pants is recommended.
    - It's Overcast outside with a temperature of +11°C in New York. Wearing a light jacket, pants, and an umbrella is recommended.
    ```

## Requirements

- Python 3.8+
- [An OpenAI API Key](https://platform.openai.com/account/api-keys)
