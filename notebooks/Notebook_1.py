# %% [markdown]
# Source notebook: Notebook_1.ipynb
# Cell order and explanatory text are preserved; saved outputs are omitted.
# See SOURCE_FILES.md at the repository root for runtime requirements.

from IPython import get_ipython as _active_ipython

def get_ipython():
    """Use the active shell and expose this script namespace to line magics."""
    shell = _active_ipython()
    if shell is None:
        raise RuntimeError("This source uses IPython commands; run it with ipython instead of python.")
    import inspect
    caller = inspect.currentframe().f_back
    shell.user_ns.update(caller.f_globals)
    shell.user_ns.update(caller.f_locals)
    return shell

# %% [markdown]
# # L1: Build your first agent
# 
# Welcome to **Building AI News Podcast Agent with Google ADK!** In this lesson, you'll build your first AI agent and give it the power to access real-time information from the web. You'll learn the fundamental structure of an agent and explore the ADK Web UI, which is a convenient way to trace your agent's thinking and interact through live voice conversations.
# 
# Throughout this course, you'll be building a complete AI News Podcast Agent that can research the latest AI developments and generate professional audio podcasts. This lesson lays the foundation with a simple agent that can fetch recent AI news from the web.
# 
# ### What you'll learn
# In this lesson, you'll build a simple agent that can fetch recent AI news from the web. An agent is a construct that has an LLM and tools:
# 
# - You'll learn about the fundamental structure of an agent
# - You'll become familiar with an **LLM** as the brain of the agent providing it the generative language capabilities
# - You'll explore **tools** that let the agent take actions in the real world
# 
# You'll also explore alternative development approaches including YAML configuration and Web Builder options.

# %% [markdown]
# ## 1.1 Getting started
# 
# The following python packages are pre-installed, but listed here for your reference. This will install a handy set of command-line tools that will be useful when working with ADK.

# %%
# Notebook cell 3
# !pip install -q google-adk>=1.12.0

# %%
# Notebook cell 4
from helper import *

# Load environment variables from .env file
load_env()

# %% [markdown]
# ## 1.2 Setting up your first agent
# 
# Before we dive into building agents, let's set up a new folder structure with ADK's built-in project scaffolding using the `adk create` command.
# 
# When you run `adk create`, it generates three essential files. 
# 1. The `.env` file securely stores your API credentials and configuration. 
# 2. The `__init__.py` file marks the directory as a Python package, nabling proper imports. 
# 3. Most importantly, the `agent.py` file provides a clean foundation where you'll implement your agent.
# 
# File structure:
# ```
# app_01/
#     __init__.py
#     agent.py
#     .env
# ```
# 
# ADK create supports two project types. The `--type=code` option generates a Python-based agent in `agent.py`. The `--type=config` option creates a YAML-based agent configuration.
# 
# The `--model` parameter specifies the LLM to be used by the agent. We will override this and experiment with different models as we create the agents in this lesson.
# 
# ### Setting up authentication
# 
# Before using any AI models, the first step is to configure API credentials. There are several methods to authenticate with Google's Gemini models, including:
# 1. Google API key and 
# 2. Vertex AI based authentication.
# 
# For more information on setting up your own authentication, visit [Google](https://cloud.google.com/free?hl=en). 
# 
# The `--api_key` parameter automatically configures your project for Google's Gemini API, setting up the proper authentication environment variables. In this course your API key is configured for you already.
# 
# Run the cell below to create the folder structure for your agent!

# %%
# Notebook cell 6
# First we create our expected agent folder 
# You can explore available option: !adk create --help 

get_ipython().system('adk create --type=code app_01 --model gemini-2.0-flash-live-001 --api_key $GEMINI_API_KEY')

# %% [markdown]
# ## 1.3 Writing your first `agent.py`
# 
# Throughout this course, you will be using the `adk create` command to create folders and then write to its agent.py using the cell magic in the notebook. Cell magic uses specific commands to interact with the files in your new agent folder. You will use `%%writefile FILENAME` to do this.
# 
# Let's start with the absolute simplest agent possible—one that has no internet access at all. You'll create an Agent with a unique name, specify the LLM model, and give it basic instructions.
# 
# As with any agent, you need an LLM to start with. ADK is model agnostic - meaning you can provide it with any model of your choice like Gemini, Claude, Ollama and even use LiteLLM to bring in other models. In this lesson, you'll be using the Gemini 2.0 flash and Gemini 2.0 flash live models.

# %%
# Notebook cell 8
get_ipython().run_cell_magic('writefile', 'app_01/agent.py', '\nfrom google.adk.agents import Agent\n\nroot_agent = Agent(\n    name="ai_news_agent_simple",\n    model="gemini-2.0-flash-live-001", # Essential for live voice interaction\n    instruction="You are an AI News Assistant.",\n)\n')

# %% [markdown]
# ## 1.4 Running your first agent
# 
# Now comes the exciting part—actually using what you've built. ADK gives you several ways to run your agent, but for development and learning, you'll use the ADK Web UI.
# 
# To start the local server and access the Web UI, follow the below steps:
# 
# **Terminal Instructions**
# 1. To open the terminal, run the cell below.
# 2. Change to the current lesson directory with the following command: `cd L1`
# 4. Start your agent using the following command: `adk web --host 0.0.0.0 --port 8001`
# 5. Run the cell below the terminal, to display the proxy URL. (This step is only needed within this codelab. When running externally, you can directly access the local server link.)
# 
# Here's a closer look at the command that starts the agent.
# - `adk web`: A simple command that starts your agent on the Web UI
# - `--host 0.0.0.0`: The host address
# - `--port 8001`: The port we will access the server from. In this case, port `8001`.

# %%
# Notebook cell 10
# start a new terminal
import os
from IPython.display import IFrame

IFrame(f"{os.environ.get('DLAI_LOCAL_URL').format(port=8888)}terminals/1", 
       width=600, height=768)

# %% [markdown]
# ### Get your app URL
# 
# **Run the cell below and open the link in a new tab.** This launches a browser-based interface for testing and debugging.
# 
# When you open the interface in your browser, you'll see the Google ADK user interface. In the left pane, select your agent from the dropdown (app_01). 
# 
# Try asking the agent a question with voice. Notice the model choice—`gemini-2.0-flash-live-001`. This is crucial because it supports Gemini Live API, enabling real-time, low-latency voice conversations.
# 
# **Voila - you have built your very first agent!** Your agent also responds with real-time, conversational voice, not just text-to-speech. It thinks and speaks in a natural flow, powered by a "live" model. The complex bidirectional audio streaming and real-time processing are handled for you automatically in the background by the ADK web UI.
# 
# **Important**: In the optional final lesson, you can explore the technical details about the bidirectional audio streaming and go over a brief overview of the architecture.

# %%
# Notebook cell 12
import os
print(os.environ.get('DLAI_LOCAL_URL').format(port='8001'))

# %% [markdown]
# ## 1.5 Adding tools to your agent
# 
# **But here's the problem:** try asking this agent about the latest AI developments, and you'll quickly discover it can only tell you about things that happened before its training cutoff date. For an AI news assistant that's supposed to fetch the latest news, that's not particularly helpful.
# 
# You need to fix that by providing your agent with **Tools**. Create another empty scaffolding folder to create an agent with a tool by running the cell below.

# %%
# Notebook cell 14
get_ipython().system('adk create --type=code app_02 --model gemini-2.0-flash-live-001 --api_key $GEMINI_API_KEY')

# %% [markdown]
# ### Adding Google Search Tool
# 
# In this scenario, to fetch the latest news, let's provide your agent with a built-in tool, `google_search`. These built-in tools come pre-packed with the library. 
# 
# To add it to the agent, just import it and provide it as a tool in the tools array. Run the cell below to import it.

# %%
# Notebook cell 16
get_ipython().run_cell_magic('writefile', 'app_02/agent.py', '\nfrom google.adk.agents import Agent\nfrom google.adk.tools import google_search\n\nroot_agent = Agent(\n    name="ai_news_agent_simple",\n    model="gemini-2.0-flash-live-001", # Essential for live voice interaction\n    instruction="You are an AI News Assistant. Use Google Search to find recent AI news.",\n    tools=[google_search]\n)\n')

# %% [markdown]
# **Refresh the ADK Web UI.** You should see a new app name (app_02) in the dropdown. Select it and start talking to your agent.
# 
# Let's test the agent with the Google search tool by asking a query "What is the latest AI News?". Watch what happens: Your agent will use the Google Search tool to find current information, process the results, and give you a comprehensive, up-to-date response with sources.
# 
# Just like that, your agent can now access **real-time information** from across the web!
# 
# ADK comes with several other powerful built-in tools—there are tools for running your code in a sandbox, querying databases, even integrations with Google Workspace tools like Calendar, Drive etc.

# %% [markdown]
# ## 1.6 Adding a text model
# So far you've been using `gemini-2.0-flash-live-001`, which is specifically designed for real-time voice interactions. But ADK supports a wide range of models, each optimized for different use cases.
# 
# Text-focused models like `gemini-2.5-flash` are ideal when you don't need voice interaction but want optimized text processing. They often provide faster response times.
# 
# Let's create a variant of your agent using a text-optimized model to see how it behaves differently.
# 
# Create a new folder for the text-based agent by running the cell below.

# %%
# Notebook cell 19
get_ipython().system('adk create --type=code app_03 --model gemini-2.5-flash --api_key $GEMINI_API_KEY')

# %% [markdown]
# Run the below cell to create a new agent. Notice how the only difference in the code is the "model" name.

# %%
# Notebook cell 21
get_ipython().run_cell_magic('writefile', 'app_03/agent.py', '\nfrom google.adk.agents import Agent\nfrom google.adk.tools import google_search\n\nroot_agent = Agent(\n    name="ai_news_agent_simple",\n    model="gemini-2.5-flash",\n    instruction="You are an AI News Assistant. Use Google Search to find recent AI news.",\n    tools=[google_search]\n)\n')

# %% [markdown]
# **Refresh the ADK Web UI**, and select the app_03 from the dropdown menu. Chat with your agent using text and ask it: "Give me the latest AI news".
# 
# *Bonus:* Explore the different capabilities in the Web UI like the Events tab.

# %% [markdown]
# ## 1.7 Alternative development approaches
# 
# ADK supports a declarative approach using YAML files. This is ideal for when you want rapid prototyping without code or want configuration or declarative style development.
# 
# Create a new folder for the agent by running the cell below. Notice that this time you use `--type=config`. This will create a new directory for your agent. 
# 
# ```
# app_04/
#     __init__.py
#     root_agent.yaml
#     .env
# ```
# 
# A new file for your agent called `root_agent.yaml` is created and you will use that to configure your agent.

# %%
# Notebook cell 24
# You can also define the agent with simple YAML confirguration 

get_ipython().system('adk create --type=config app_04 --model gemini-2.5-flash --api_key $GEMINI_API_KEY')

# %% [markdown]
# ### Building agents with the YAML configuration
# 
# The config below maps directly to our Python version. You define the same core components—name, model, instructions, and tools—but in a declarative format. The schema validation ensures your configuration is correct.
# 
# Now, **refresh the ADK Web UI** and switch to the yaml version in the UI (select app_04 in the dropdown). Try interacting with the agent using voice and verify it is fully functional.

# %%
# Notebook cell 26
get_ipython().run_cell_magic('writefile', 'app_04/root_agent.yaml', '\nname: ai_news_agent_yaml\nmodel: gemini-2.0-flash-live-001 # Using a model that supports live voice\ndescription: An agent that answers questions about recent news in Artificial Intelligence.\ninstruction: You are an AI News Assistant. Use Google Search to find and summarize recent AI news.\ntools:\n  - name: google_search\n')

# %% [markdown]
# ## 1.8 Fine-tuning agent instructions
# 
# So far your agent has simple instructions, but for reliable behavior, you need more sophisticated instruction engineering. Let's enhance your agent with strict behavioral controls.
# 
# Create a new folder using the `adk create` command.

# %%
# Notebook cell 28
# You can also modify the instructions  

get_ipython().system('adk create --type=code app_05 --model gemini-2.0-flash-live-001 --api_key $GEMINI_API_KEY')

# %% [markdown]
# Write the updated agent code to the `agent.py` file.

# %%
# Notebook cell 30
get_ipython().run_cell_magic('writefile', 'app_05/agent.py', '\nfrom google.adk.agents import Agent\nfrom google.adk.tools import google_search\n\nroot_agent = Agent(\n    name="ai_news_agent_strict",\n    model="gemini-2.0-flash-live-001",\n    instruction="""\n    **Your Core Identity and Sole Purpose:**\n    You are a specialized AI News Assistant. Your sole and exclusive purpose is to find and summarize recent news (from the last few weeks) about Artificial Intelligence.\n\n    **Strict Refusal Mandate:**\n    If a user asks about ANY topic that is not recent AI news, you MUST refuse.\n    For off-topic requests, respond with the exact phrase: "Sorry, I can\'t answer anything about this. I am only supposed to answer about the latest AI news."\n\n    **Required Workflow for Valid Requests:**\n    1. You MUST use the `google_search` tool to find information.\n    2. You MUST base your answer strictly on the search results.\n    3. You MUST cite your sources.\n    """,\n    tools=[google_search]\n)\n')

# %% [markdown]
# ### Understanding Advanced Instructions
# 
# This enhanced instruction pattern includes:
# 
# - **Clear Identity**: Explicitly defines the agent's sole purpose
# - **Refusal Mechanism**: Provides exact phrases for rejecting off-topic requests  
# - **Workflow Requirements**: Forces the agent to use tools and cite sources
# - **Behavioral Boundaries**: Sets expectations for valid vs. invalid requests
# 
# This creates a much more reliable and focused agent behavior.
# 
# ### Testing Instructions
# 
# **Refresh the ADK Web UI**, select the appropriate app (app_05) from the dropdown menu and test your enhanced agent with both valid and invalid requests:
# 
# **Valid prompts** (should get a response):
# - "What's the latest AI news about Google?"
# - "Tell me about recent AI chip developments"
# 
# **Invalid prompts** (should be refused):
# - "What's the weather today?"
# - "Help me with my homework"
# 
# Watch how the agent now maintains strict boundaries while still being helpful for AI-related queries.

# %% [markdown]
# # 🚨 **IMPORTANT** 🚨
# 
# After finishing, make sure to run the cell below to close your connection so it does not interfere as you progress through the notebooks.

# %%
# Notebook cell 33
# Kill ADK process
get_ipython().system('pkill -f "adk web"')

# %% [markdown]
# <p style="background-color:#f7fff8; padding:15px; border-width:3px; border-color:#e0f0e0; border-style:solid; border-radius:6px"> 🚨
# &nbsp; <b>Different Run Results:</b> The output generated by AI chat models can vary with each execution due to their dynamic, probabilistic nature. Don't be surprised if your results differ from those shown in the video.</p>

# %% [markdown]
# <div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
# <p> 💻 &nbsp; <b> To Access the <code>requirements.txt</code> file or the <code>papers</code> folder: </b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em> and finally 3) click on <em>"L1"</em>.
# </div>

# %% [markdown]
# <div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
# 
# 
# <p> ⬇ &nbsp; <b>Download Notebooks:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Download as"</em> and select <em>"Notebook (.ipynb)"</em>.</p>
# 
# </div>

# %% [markdown]
# # Resources
# 
# [Gemini API Models](https://ai.google.dev/gemini-api/docs/models#model-variations)
