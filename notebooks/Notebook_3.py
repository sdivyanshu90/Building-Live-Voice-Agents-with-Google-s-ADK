# %% [markdown]
# Source notebook: Notebook_3.ipynb
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
# # L4: Adding a Research Agent

# %% [markdown]
# In this lesson, you'll transform your agent from a conversational interface into a research coordinator that works behind the scenes. You'll learn to implement a **coordinator-dispatcher** pattern where the root agent delegates research work to background processes and saves structured reports for later use.
# 
# This architectural shift is crucial for building production AI systems that can handle complex workflows without overwhelming users with intermediate processing details.
# 
# **Key Learning Objectives:**
# 
# - Create coordinator agents that delegate work silently
# - Build agents optimized for background processing
# - Implement file persistence with structured markdown reports
# - Understand when to use structured schemas vs. free-form output
# 
# **Note:** This lesson introduces patterns essential for multi-agent systems and production deployment.

# %% [markdown]
# ## 4.1 Getting Started
# The following python packages are pre-installed, but listed here for your reference. This will install a handy set of command-line tools that will be useful when working with ADK.

# %%
# Notebook cell 4
# !pip install google-adk>=1.12.0
# !pip install yfinance

# %%
# Notebook cell 5
from helper import *

# Load environment variables from .env file
load_env()

# %% [markdown]
# ## 4.2 Setting up your agent
# The first step is to create the ADK folder, just like you've done in the previous lessons.

# %%
# Notebook cell 7
# First we create our expected agent folder 
# You can explore available option: !adk create --help 

get_ipython().system('adk create --type=code app04 --model gemini-2.0-flash-live-001 --api_key $GEMINI_API_KEY')

# %% [markdown]
# ## 4.3 The Coordinator-Dispatcher Architecture Pattern
# In this lesson, you'll be implementing a sophisticated architectural pattern that separates user interaction from background processing. This pattern is essential for production AI systems.
# 
# ### The Challenge: Information Overload
# In previous lessons, your agent would research news and immediately read all findings to the user. This creates several problems:
# 
# - **Cognitive overload**: Users get overwhelmed with raw research data  
# - **Poor user experience**: Long delays while listening to unfiltered information  
# - **Inefficient workflows**: No separation between data gathering and content creation  
# 
# ### The Solution: Coordinator-Dispatcher Pattern
# The coordinator-dispatcher pattern solves this by implementing a two-phase workflow:
# 
# 1. **Coordination Phase**: Root agent acknowledges the request and coordinates background work  
# 2. **Execution Phase**: Agent silently executes research, analysis, and file persistence  
# 
# ### Implementation Strategy
# You'll add a save_news_to_markdown tool that:
# 
# - Takes research from google_search and get_financial_context  
# - Structures the data into a readable markdown report  
# - Saves results as ai_research_report.md  
# - Enables the root agent to work as a coordinator, not a presenter  
# 
# This architectural shift prepares you for the podcast generation system you'll build in later lessons.
# 
# ### Financial Context Tool: Reusing Existing Components
# You'll start by implementing the same financial data tool from Lesson 2.

# %%
# Notebook cell 9
get_ipython().run_cell_magic('writefile', 'app04/agent.py', 'import pathlib\nfrom typing import Dict, List\nimport yfinance as yf\n\nfrom google.adk.agents import Agent\nfrom google.adk.tools import google_search\n\n\ndef get_financial_context(tickers: List[str]) -> Dict[str, str]:\n    """\n    Fetches the current stock price and daily change for a list of stock tickers\n    using the yfinance library.\n\n    Args:\n        tickers: A list of stock market tickers (e.g., ["NVDA", "MSFT"]).\n\n    Returns:\n        A dictionary mapping each ticker to its formatted financial data string.\n    """\n    financial_data: Dict[str, str] = {}\n    for ticker_symbol in tickers:\n        try:\n            # Create a Ticker object\n            stock = yf.Ticker(ticker_symbol)\n\n            # Fetch the info dictionary\n            info = stock.info\n\n            # Safely access the required data points\n            price = info.get("currentPrice") or info.get("regularMarketPrice")\n            change_percent = info.get("regularMarketChangePercent")\n\n            if price is not None and change_percent is not None:\n                # Format the percentage and the final string\n                change_str = f"{change_percent * 100:+.2f}%"\n                financial_data[ticker_symbol] = f"${price:.2f} ({change_str})"\n            else:\n                # Handle cases where the ticker is valid but data is missing\n                financial_data[ticker_symbol] = "Price data not available."\n\n        except Exception:\n            # This handles invalid tickers or other yfinance errors gracefully\n            financial_data[ticker_symbol] = "Invalid Ticker or Data Error"\n\n    return financial_data\n')

# %% [markdown]
# ## 4.4 File Persistence Tool: Creating Structured Reports
# Now you'll implement a tool that saves research results to persistent storage, providing us with downloadable, shareable reports.

# %%
# Notebook cell 11
get_ipython().run_cell_magic('writefile', '-a app04/agent.py', '\ndef save_news_to_markdown(filename: str, content: str) -> Dict[str, str]:\n    """\n    Saves the given content to a Markdown file in the current directory.\n\n    Args:\n        filename: The name of the file to save (e.g., \'ai_news.md\').\n        content: The Markdown-formatted string to write to the file.\n\n    Returns:\n        A dictionary with the status of the operation.\n    """\n    try:\n        if not filename.endswith(".md"):\n            filename += ".md"\n        current_directory = pathlib.Path.cwd()\n        file_path = current_directory / filename\n        file_path.write_text(content, encoding="utf-8")\n        return {\n            "status": "success",\n            "message": f"Successfully saved news to {file_path.resolve()}",\n        }\n    except Exception as e:\n        return {"status": "error", "message": f"Failed to save file: {str(e)}"}\n')

# %% [markdown]
# ## 4.5 Advanced Agent Instructions: Implementing Coordinator Behavior
# 
# ### Adding a root agent
# Now you'll configure your agent with sophisticated instructions that implement the coordinator-dispatcher pattern.
# 
# ### Key Architectural Changes
# Compared to previous agents, you'll be implenting  several critical improvements using instructions that demonstrate several advanced patterns:
# 
# - **Explicit role definition**: Provide a clear identity as "background research coordinator"
# - **Strict workflow specification**: Step-by-step execution requirements
# - **Output schema enforcement**: Exact format requirements for consistency
# - **Error Handling**: Graceful failure modes at each step and
# - **Behavioral Constraints**

# %%
# Notebook cell 13
get_ipython().run_cell_magic('writefile', '-a app04/agent.py', '\n# The root_agent is what ADK will run.\nroot_agent = Agent(\n    name="ai_news_research_coordinator",\n    model="gemini-1.5-pro",\n    instruction="""\n    **Your Identity:** You are a background AI Research Coordinator. Your sole purpose is to respond to requests for \n    recent AI news by performing a multi-step research task and saving the result to a file.\n\n    **Strict Topic Mandate:**\n    If a user asks about anything other than recent AI news, you MUST refuse with the exact phrase: "Sorry, I can only help \n    with recent AI news."\n\n    **Required Two-Message Interaction Workflow:**\n\n    1.  **Initial Acknowledgment:** The MOMENT you receive a valid request for AI news, your first and only immediate \n    response MUST be:\n        *   "Okay, I\'ll start researching the latest AI news. I will enrich the findings with financial data and compile a \n        report for you. This might take a moment."\n\n    2.  **Background Processing (Silent):** After sending the acknowledgment, you will silently execute the following \n    sequence of tool calls without any further communication with the user:\n        a.  **Search:** Use the `google_search` tool to find 5 recent, relevant news articles about AI, focusing on \n        US-listed companies.\n        b.  **Extract Tickers:** Internally, identify the stock ticker for each company mentioned (e.g., \'NVDA\' for Nvidia).\n        c.  **Get Financial Data:** Call the `get_financial_context` tool with the list of extracted tickers.\n        d.  **Format Report:** Construct a single Markdown string for the report. You MUST format this string to \n        EXACTLY match the schema below.\n\n    **Required Report Schema:**\n    ```markdown\n    # AI Industry News Report\n\n    ## Top Headlines\n\n    ### 1. {News Headline 1}\n    *   **Company:** {Company Name} ({Ticker Symbol})\n    *   **Market Data:** {Stock Price and % Change from get_financial_context}\n    *   **Summary:** {Brief, 1-2 sentence summary of the news.}\n\n    ### 2. {News Headline 2}\n    *   **Company:** {Company Name} ({Ticker Symbol})\n    *   **Market Data:** {Stock Price and % Change from get_financial_context}\n    *   **Summary:** {Brief, 1-2 sentence summary of the news.}\n\n    (Continue for all 5 news items)\n    ```\n        e.  **Save Report:** Call the `save_news_to_markdown` tool with the filename `ai_research_report.md` and the fully \n        formatted Markdown string as the content.\n\n    3.  **Final Confirmation:** Once `save_news_to_markdown` returns a success message, your second and final response to the \n    user MUST be:\n        *   "All done. I\'ve compiled the research report with the latest financial context and saved it to \n        `ai_research_report.md`."\n\n    **Crucial Rule:** All complex work happens silently in the background between your initial acknowledgment and\n    your final confirmation. Do not engage in any other conversation.\n    """,\n    tools=[google_search, get_financial_context, save_news_to_markdown],\n)\n')

# %% [markdown]
# ## 4.6 Test Your Agent
# Let's test your agent using the ADK Web UI. These steps will be repeated for all lessons in this course.
# 
# 1. Run the cell below to start a new terminal.
# 2. In the new terminal, navigate to the L4 directory using the following command `cd L4`
# 3. Then, in the terminal, start the ADK web server using the command  
# 4. `adk web --host 0.0.0.0 --port 8004`
# 5. Remember to hit `Ctrl + C` in the terminal when you are finished testing your agent

# %%
# Notebook cell 15
# start a new terminal
import os
from IPython.display import IFrame

IFrame(f"{os.environ.get('DLAI_LOCAL_URL').format(port=8888)}terminals/4", 
       width=600, height=768)

# %% [markdown]
# <p style="background-color:#f7fff8; padding:15px; border-width:3px; border-color:#e0f0e0; border-style:solid; border-radius:6px"> 🔄
# &nbsp; <b>Starting the ADK Server:</b> After starting a new terminal window, it may take a few seconds to get a new command line prompt. 

# %% [markdown]
# ### Get your application URL
# After you start the Google ADK server, run the following command to get the URL where you can access your app: 

# %%
# Notebook cell 18
import os
print(os.environ.get('DLAI_LOCAL_URL').format(port='8004'))

# %% [markdown]
# <div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
# 
# ### Gathering and Saving Output
# - Once you start the app, say something like "Get me the latest news about artifical intelligence."
# - The agent will ask you how many articles you want it to return, provide it with any number. 
# - A search will be performed behind the scences, and when the agent has finished saving the results to a file, it will provide you with a voice confirmation. This may take a few minutes. 
# - Once you get a voice confirmation from the agent, you can move on to the next step- reading in the file and viewing your results. 

# %% [markdown]
# ## 4.7 Viewing the output
# The following function will read in the .md file with the news results fetched by your agent. You can see that the output is clearly formatted by the instructions provided when creating the root agent. 

# %%
# Notebook cell 21
from IPython.display import Markdown, display

# Read and display the markdown file
with open('ai_research_report.md', 'r', encoding='utf-8') as f:
    content = f.read()

display(Markdown(content))

# %% [markdown]
# # 🚨 **IMPORTANT** 🚨
# 
# After finishing, make sure to run the cell below to close your connection so it does not interfere as you progress through the notebooks.

# %%
# Notebook cell 23
# Terminate ADK process
get_ipython().system('pkill -f "adk web"')

# %% [markdown]
# <p style="background-color:#f7fff8; padding:15px; border-width:3px; border-color:#e0f0e0; border-style:solid; border-radius:6px"> 🚨
# &nbsp; <b>Different Run Results:</b> The output generated by AI chat models can vary with each execution due to their dynamic, probabilistic nature. Don't be surprised if your results differ from those shown in the video.</p>

# %% [markdown]
# <div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
# <p> 💻 &nbsp; <b> To Access the <code>requirements.txt</code> file or the <code>papers</code> folder: </b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em> and finally 3) click on <em>"L4"</em>.
# </div>

# %% [markdown]
# <div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
# 
# 
# <p> ⬇ &nbsp; <b>Download Notebooks:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Download as"</em> and select <em>"Notebook (.ipynb)"</em>.</p>
# 
# </div>
