# %% [markdown]
# Source notebook: Notebook_2.ipynb
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
# # L3: Tools for your agent
# Welcome to Lesson 3 **Tools for your agent**. In this lesson, you'll learn how to add custom function tools and enhance your agent with external data sources. You'll integrate financial data APIs and build more sophisticated agent instructions—essential skills for building reliable AI applications.
# 
# ### Building on previous lessons:
# - **Lesson 1**: Basic agents with Google search capabilities
# - **Lesson 2**: Session, State & Memory in agents
# 
# ### What's new in Lesson 3:
# This lesson teaches you to extend agents beyond basic web search by adding custom tools that interact with external APIs and data sources.
# 
# ## 3.1 Getting Started
# The following python packages are pre-installed, but listed here for your reference. This will install a handy set of command-line tools that will be useful when working with ADK.

# %%
# Notebook cell 2
# !pip install -q google-adk>=1.12.0
# !pip install yfinance

# %%
# Notebook cell 3
from helper import *

# Load environment variables from .env file
load_env()

# %% [markdown]
# ## 3.2 Setting up your agent
# The first step is to create the ADK folder, just like you've done in the previous lessons. 

# %%
# Notebook cell 5
# First we create our expected agent folder 
# You can explore available option: !adk create --help 

get_ipython().system('adk create --type=code app03 --model gemini-2.0-flash-live-001 --api_key $GEMINI_API_KEY')

# %% [markdown]
# ## 3.3 Building a Custom Function Tool
# Now you'll create your first **custom function tool**. In ADK, a Function Tool is a modular code component that gives your agent specific capabilities to interact with external systems or process data.
# 
# ### Adding the Financial Tool
# Let's break down the key components of this function tool:
# 
# - **Type Annotations**: List[str] and Dict[str, str] enable ADK's automatic schema generation  
# - **Comprehensive Docstring**: The docstring becomes the tool's description that the agent sees  
# - **Error Handling**: Try-catch blocks ensure graceful failures for invalid tickers or network issues  
# - **Consistent Output**: Always returns a dictionary with formatted strings, even for errors  
# 
# This tool fetches current stock prices and daily percentage changes using the Yahoo Finance API through the yfinance library.

# %%
# Notebook cell 7
get_ipython().run_cell_magic('writefile', 'app03/agent.py', '\nfrom typing import Dict, List\nfrom google.adk.agents import Agent\nfrom google.adk.tools import google_search\nimport yfinance as yf\n\ndef get_financial_context(tickers: List[str]) -> Dict[str, str]:\n    """\n    Fetches the current stock price and daily change for a list of stock tickers\n    using the yfinance library.\n\n    Args:\n        tickers: A list of stock market tickers (e.g., ["GOOG", "NVDA"]).\n\n    Returns:\n        A dictionary mapping each ticker to its formatted financial data string.\n    """\n    financial_data: Dict[str, str] = {}\n    for ticker_symbol in tickers:\n        try:\n            # Create a Ticker object\n            stock = yf.Ticker(ticker_symbol)\n\n            # Fetch the info dictionary\n            info = stock.info\n\n            # Safely access the required data points\n            price = info.get("currentPrice") or info.get("regularMarketPrice")\n            change_percent = info.get("regularMarketChangePercent")\n\n            if price is not None and change_percent is not None:\n                # Format the percentage and the final string\n                change_str = f"{change_percent * 100:+.2f}%"\n                financial_data[ticker_symbol] = f"${price:.2f} ({change_str})"\n            else:\n                # Handle cases where the ticker is valid but data is missing\n                financial_data[ticker_symbol] = "Price data not available."\n\n        except Exception:\n            # This handles invalid tickers or other yfinance errors gracefully\n            financial_data[ticker_symbol] = "Invalid Ticker or Data Error"\n\n    return financial_data\n')

# %% [markdown]
# ### Understanding Function Tools
# What makes a good function tool:
# 
# - **Clear Documentation**: Comprehensive docstrings that ADK uses for tool descriptions  
# - **Type Annotations**: Essential for ADK's automatic tool registration and schema validation  
# - **Robust Error Handling**: Graceful failure modes prevent agent crashes  
# - **Consistent Return Format**: Predictable output structure agents can reliably process  
# 
# ## 3.4 Adding your root agent 
# Now let's create your agent with sophisticated instructions that use both the Google Search tool and your custom financial tool.
# 
# Let's examine the enhanced instructions:
# 
# ### Key Instruction Patterns
# Notice how these instructions implement several best practices:
# 
# 1. **Structured Workflow**: 5-step process from clarification to detailed discussion  
# 2. **Tool Citation Requirements**: Agent must cite google_search and get_financial_context usage  
# 3. **Interactive Design**: Prompts user for input at each stage rather than providing monologues  
# 4. **Scope Boundaries**: Clear rules about staying focused on AI news for US-listed companies  
# 5. **Error Handling**: Graceful responses when asked about off-topic subjects  
# 
# This creates a much more reliable and user-friendly conversational experience.

# %%
# Notebook cell 9
get_ipython().run_cell_magic('writefile', '-a app03/agent.py', '\nroot_agent = Agent(\n    name="ai_news_chat_assistant",\n    model="gemini-2.0-flash-live-001",\n    instruction="""\n    You are an AI News Analyst specializing in recent AI news about US-listed companies. Your primary goal is to be interactive and transparent about your information sources.\n\n    **Your Workflow:**\n\n    1.  **Clarify First:** If the user makes a general request for news (e.g., "give me AI news"), your very first response MUST be to ask for more details.\n        *   **Your Response:** "Sure, I can do that. How many news items would you like me to find?"\n        *   Wait for their answer before doing anything else.\n\n    2.  **Search and Enrich:** Once the user specifies a number, perform the following steps:\n        *   Use the `google_search` tool to find the requested number of recent AI news articles.\n        *   For each article, identify the US-listed company and its stock ticker.\n        *   Use the `get_financial_context` tool to retrieve the stock data for the identified tickers.\n\n    3.  **Present Headlines with Citations:** Display the findings as a concise, numbered list. You MUST cite your tools.\n        *   **Start with:** "Using `google_search` for news and `get_financial_context` (via yfinance) for market data, here are the top headlines:"\n        *   **Format:**\n            1.  [Headline 1] - [Company Stock Info]\n            2.  [Headline 2] - [Company Stock Info]\n\n    4.  **Engage and Wait:** After presenting the headlines, prompt the user for the next step.\n        *   **Your Response:** "Which of these are you interested in? Or should I search for more?"\n\n    5.  **Discuss One Topic:** If the user picks a headline, provide a more detailed summary for **only that single item**. Then, re-engage the user.\n\n    **Strict Rules:**\n    *   **Stay on Topic:** You ONLY discuss AI news related to US-listed companies. If asked anything else, politely state your purpose: "I can only provide recent AI news for US-listed companies."\n    *   **Short Turns:** Keep your responses brief and always hand the conversation back to the user. Avoid long monologues.\n    *   **Cite Your Tools:** Always mention `google_search` when presenting news and `get_financial_context` when presenting financial data.\n    """,\n    tools=[google_search, get_financial_context],\n)\n')

# %% [markdown]
# ## 3.5 Test Your Agent
# Let's test your agent using the ADK Web UI. These steps will be repeated for all lessons in this course.
# 
# 1. Run the below cell to start a new terminal.
# 2. In the terminal, navigate to the L3 directory using the following command `cd L3`
# 3. In the terminal, start the ADK web server using the command `adk web --host 0.0.0.0 --port 8003`

# %% [markdown]
# <p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>Iframe Terminal</code>:</b> Once you run the following cell, it can take a few seconds to start a new terminal window in the Jupyter Notebook cell.</p>

# %%
# Notebook cell 12
# start a new terminal
import os
from IPython.display import IFrame

IFrame(f"{os.environ.get('DLAI_LOCAL_URL').format(port=8888)}terminals/3", 
       width=600, height=768)


# adk web --host 0.0.0.0 --port 8003

# %% [markdown]
# ### Get your application URL
# After you start the Google ADK server, run the following cell to get the URL where you can access your agent in the ADK Web UI: 

# %%
# Notebook cell 14
import os
print(os.environ.get('DLAI_LOCAL_URL').format(port='8003'))

# %% [markdown]
# <p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Remember:</b> Stop the ADK web server before moving to the next section by running the following line of code:  <b>!pkill -f "adk web"</b></p>

# %% [markdown]
# ### Try This Testing Sequence
# Once your agent is running, try this conversation flow to see all the features in action:
# 
# 1. Start with a general request: "Give me AI news for Google"  
# 2. Respond to clarification: "Give me 3 top AI news items for publicly traded US tech stocks"  
# 3. Pick a specific story: "Tell me more about the first one"  
# 4. Test boundaries: "What's the weather today?" (should be refused)  
# 
# Watch how the agent uses both tools in coordination and maintains conversation flow.

# %% [markdown]
# <p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note:Tool Coordination</b> Watch how your agent coordinates between the two tools. It first uses `google_search` to find AI news articles, then identifies company tickers mentioned in those articles, and finally calls `get_financial_context` to enrich the news with current stock information. This demonstrates how multiple tools can work together to provide comprehensive responses.</p>

# %% [markdown]
# ## 🎯 3.6 Exercise: Expand Your Tool
# Now it's your turn to experiment and enhance the agent! Try these modifications:
# 
# ### Exercise 1: Add Another Custom Tool
# Create a new custom tool and add it to your agent. Here are some ideas:
# 
# - **Company Info Tool**: Use an API to get company details (headquarters, CEO, employee count)
# - **News Sentiment Tool**: Analyze the sentiment of news headlines (positive/negative/neutral)
# - **Market Summary Tool**: Get overall market indices (S&P 500, NASDAQ, Dow Jones)
# - **AI Trends Tool**: Track mentions of specific AI technologies (LLM, computer vision, robotics)
# 
# **Hint**: Follow the same pattern as get_financial_context - include type annotations, comprehensive docstrings, and robust error handling. 
# 
# Don't forget to add your new tool to the agent's tools array!
# 
# ### Exercise 2: Instruction Refinement
# Enhance the agent instructions to:
# 
# - Request user preference for number of companies to track (1-5 range)
# - Add a disclaimer about financial data being for informational purposes only
# - Include timestamp information about when the data was fetched
# 
# ### Exercise 3: Conversation Flow
# Test the conversation boundaries:
# 
# - Try asking about non-US companies and see how the agent responds
# - Test with different types of AI news (research, products, acquisitions)
# - See how the agent handles follow-up questions about specific companies
# 
# ### Exercise 4: Error Handling
# Test the tool's error handling:
# 
# - Try requesting financial data for invalid ticker symbols
# - Test with companies that might not have complete financial data
# - See how the agent handles network connectivity issues
# 
# **Pro Tip**: Use the `--reload_agents` flag when starting `adk web` so you can iterate quickly!

# %% [markdown]
# ## 3.7 📚 References and Additional Resources
# ### Official Documentation
# - [Google ADK Tools Guide](https://google.github.io/adk-docs/tools/)
# - [Function Tools Documentation](https://google.github.io/adk-docs/tools/function-tools/)
# - [yfinance Library Documentation](https://pypi.org/project/yfinance/)
# 
# ### Key Concepts Covered
# - **Custom Function Tools:** Python functions that extend agent capabilities
# - **Tool Coordination:** Using multiple tools together for comprehensive responses
# - **Type Annotations:** Essential for ADK's automatic tool registration
# - **Error Handling:** Building robust tools that handle edge cases gracefully
# - **Interactive Agent Design:** Creating conversational agents that engage users
# 
# ### Advanced Tool Patterns
# - **Tool Composition:** Combining outputs from multiple tools
# - **Conditional Tool Usage:** Using tools based on user input or context
# - **Tool Citations:** Transparent tool usage reporting
# - **Graceful Degradation:** Handling tool failures elegantly

# %% [markdown]
# # 🚨 **IMPORTANT** 🚨
# 
# After finishing, make sure to run the cell below to close your connection so it does not interfere as you progress through the notebooks.

# %%
# Notebook cell 21
# Kill ADK process
get_ipython().system('pkill -f "adk web"')

# %% [markdown]
# <p style="background-color:#f7fff8; padding:15px; border-width:3px; border-color:#e0f0e0; border-style:solid; border-radius:6px"> 🚨
# &nbsp; <b>Different Run Results:</b> The output generated by AI chat models can vary with each execution due to their dynamic, probabilistic nature. Don't be surprised if your results differ from those shown in the video.</p>

# %% [markdown]
# <div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
# <p> 💻 &nbsp; <b> To Access the <code>requirements.txt</code> file or the <code>papers</code> folder: </b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em> and finally 3) click on <em>"L3"</em>.
# </div>

# %% [markdown]
# <div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
# 
# 
# <p> ⬇ &nbsp; <b>Download Notebooks:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Download as"</em> and select <em>"Notebook (.ipynb)"</em>.</p>
# 
# </div>

# %% [markdown]
# ### What's Next
# In **Lesson 4**, you'll learn to how to implement structured output using Pydantic schemas to ensure consistent, reliable agent responses.
# 
# You've now built an agent that combines web search with real-time financial data—a powerful pattern for building practical AI applications! 🚀
