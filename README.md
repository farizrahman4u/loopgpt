
<H1>
<p align="center">
  L♾️pGPT
</p>
</H1>
<p align="center">
    <b>A Modular Auto-GPT Framework</b>
</p>

<p align="center">
    <a href="https://discord.gg/rqs26cqx7v">
        <img src="https://img.shields.io/discord/1098162593291587594?style=for-the-badge">
    </a>
</p>




L♾️pGPT is a re-implementation of the popular [Auto-GPT](https://github.com/Significant-Gravitas/Auto-GPT) project as a proper python package, written with modularity and extensibility in mind.

## 🚀 Features 🚀

*  **"Plug N Play" API** - Extensible and modular "Pythonic" framework, not just a command line tool. Easy to add new features, integrations and custom agent capabilities, all from python code, no nasty config files!
*  **GPT 3.5 friendly** - Better results than Auto-GPT for those who don't have GPT-4 access yet!
*  **Minimal prompt overhead** - Every token counts. We are continuously working on getting the best results with the least possible number of tokens.
*  **Human in the Loop** - Ability to "course correct" agents who go astray via human feedback.
*  **Full state serialization** - Pick up where you left off; L♾️pGPT can save the complete state of an agent, including memory and the states of its tools to a file or python object. No external databases or vector stores required (but they are still supported)!


## 🧑‍💻 Installation

### Install from PyPI

📗 **This installs the latest stable version of L♾️pGPT. This is recommended for most users:**

```bash
pip install loopgpt
```

📕 The below two methods install the latest development version of L♾️pGPT. Note that this version maybe unstable:

### Install from source

```bash
pip install git+https://www.github.com/farizrahman4u/loopgpt.git@main
```

### Install from source (dev)

```bash
git clone https://www.github.com/farizrahman4u/loopgpt.git
cd  loopgpt
pip install -e .
```

### Install from source (dev) using Docker
```bash
git clone https://www.github.com/farizrahman4u/loopgpt.git
cd  loopgpt
docker build -t loopgpt:local-dev .
```

## 🏎️ Getting Started

### Setup your OpenAI API Key 🔑

#### Option 1️⃣: Via a `.env` file

Create a `.env` file in your current working directory (wherever you are going to run L♾️pGPT from) and add the following line to it:

```bash
OPENAI_API_KEY="<your-openai-api-key>"
```

🛑 **IMPORTANT** 🛑

Windows users, please make sure "show file extensions" is enabled in your file explorer. Otherwise, your file will be named `.env.txt` instead of `.env`.

#### Option 2️⃣: Via environment variables

Set an environment variable called `OPENAI_API_KEY` to your OpenAI API Key.

How to set environment variables:
- [Windows](https://www.architectryan.com/2018/08/31/how-to-change-environment-variables-on-windows-10/)
- [Linux](https://www.freecodecamp.org/news/how-to-set-an-environment-variable-in-linux/)
- [Mac](https://phoenixnap.com/kb/set-environment-variable-mac)

### Create a new L♾️pGPT Agent🕵️:

Let's create an agent in a new [Python](https://python.org) script.

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

Save your Python file as `research_gpt.py` and run it:

```bash
python research_gpt.py
```

<img src="/docs/assets/imgs/loopgpt_demo_pic.png?raw=true" height="350">

You can exit the CLI by typing "exit".

### 🔁 Continuous Mode 🔁

If `continuous` is set to `True`, the agent will not ask for the user's permission to execute commands. It may go into infinite loops, so use it at your own risk!

```python
agent.cli(continuous=True)
```

### 💻 Command Line Only Mode

You can run L♾️pGPT directly from the command line without having to write any python code as well:

```bash
loopgpt run
```

Run `loopgpt --help` to see all the available options.

### 🐋 Docker Mode

You can run L♾️pGPT in the previously mentioned modes, using Docker:

```bash
# CLI mode
docker run -i --rm loopgpt:local-dev loopgpt run

# Script mode example
docker run -i --rm -v "$(pwd)/scripts:/scripts" loopgpt:local-dev python /scripts/myscript.py

```

## ⚒️ Adding custom tools ⚒️

L♾️pGPT agents come with a set of builtin tools which allows them to perform various basic tasks such as searching the web, filesystem operations, etc. You can view these tools with `print(agent.tools)`.

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
        return {"city": "name of the city"}
    
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
            return {"report": f"An error occurred while getting the weather: {e}."}
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

Let's take a look at the `dressing_tips.txt` file that WeatherGPT wrote for us:

dressing_tips.txt
```
- It's Clear outside with a temperature of +10°C in Beijing. Wearing a light jacket and pants is recommended.
- It's Overcast outside with a temperature of +11°C in New York. Wearing a light jacket, pants, and an umbrella is recommended.
```

## 🚢 Course Correction

Unlike Auto-GPT, the agent does not terminate when the user denies the execution of a command. Instead it asks the user for feedback to correct its course.

To correct the agent's course, just deny execution and provide feedback:

<img src="/docs/assets/imgs/course_correction_1.png?raw=true">

The agent has updated its course of action:

<img src="/docs/assets/imgs/course_correction_2.png?raw=true">


## 💾 Saving and Loading Agent State 💾

You can save an agent's state to a json file with:

```python
agent.save("ResearchGPT.json")
```

This saves the agent's configuration (model, name, description etc) as well as its internal state (conversation state, memory, tool states etc).
You can also save just the confifguration by passing `include_state=False` to `agent.save()`:

```python
agent.save("ResearchGPT.json", include_state=False)
```

Then pick up where you left off with:

```python
import loopgpt
agent = loopgpt.Agent.load("ResearchGPT.json")
agent.cli()
```

or by running the saved agent from the command line:

```bash
loopgpt run ResearchGPT.json
```

You can convert the agent state to a json compatible python dictionary instead of writing to a file:

```python
agent_config = agent.config()
```

To get just the configuration without the internal state:

```python
agent_config = agent.config(include_state=False)
```


To reload the agent from the config, use:

```python
import loopgpt

agent = loopgpt.Agent.from_config(agent_config)
```

## 📋 Requirements

- Python 3.8+
- [An OpenAI API Key](https://platform.openai.com/account/api-keys)
- Google Chrome

### Optional Requirements

For official google search support you will need to setup two environment variable keys `GOOGLE_API_KEY` and `CUSTOM_SEARCH_ENGINE_ID`, here is how to get them:

1. Create an application on the [Google Developers Console][google-console].
2. Create your custom search engine using [Google Custom Search][google-custom-search].
3. Once your custom search engine is created, select it and get into the details page of the search engine.
    - On the "Basic" section, you will find the "Search engine ID" field, that value is what you will use for the `CUSTOM_SEARCH_ENGINE_ID` environment variable.
    - Now go to the "Programmatic Access" section at the bottom of the page.
        - Create a "Custom Search JSON API"
        - Follow the dialog by selecting the application you created on step #1 and when you get your API key use it to populate the `GOOGLE_API_KEY` environment variable.

ℹ️ In case these are absent, L♾️pGPT will fall back to using [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/).

## 💌 Contribute 

We need A LOT of Help! Please open an issue or a PR if you'd like to contribute.

## 🌳 Community

Need help? Join our [Discord](https://discord.gg/rqs26cqx7v).

[google-console]: https://console.developers.google.com
[google-custom-search]: https://programmablesearchengine.google.com/controlpanel/create


## ⭐ Star History 📈
<img src="https://api.star-history.com/svg?repos=farizrahman4u/loopgpt&type=Date" alt= "Star History Chart" height="350">
