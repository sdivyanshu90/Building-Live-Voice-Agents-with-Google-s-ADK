# %% [markdown]
# Source notebook: Notebook_4.ipynb
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
# # L5: Instruction Tuning and Guardrails
# 
# In this lesson, you'll take everything you've learned from previous lessons and add advanced control mechanisms that transform your agents from helpful assistants into specialized, production-ready systems.
# 
# ### Building on previous lessons
# 
# So far in this course, you've built:
# 
# - **Lesson 1**: Basic agents with Google search capabilities
# - **Lesson 2**: Session, State & Memory in agents
# - **Lesson 3**: Interactive chat agents with financial data integration (`get_financial_context`)  
# - **Lesson 4**: Coordinator agents with file persistence (`save_news_to_markdown`) and structured workflows
# 
# ### What's new in Lesson 5
# 
# Now you'll add another piece: **programmatic control systems** to ensure your agents behave reliably in production environments:
# 
# - **Callback Systems**: Programmatic guardrails that automatically enforce policies
#     1. **Domain Filtering**: Before Tool callback that blocks certain sources thus controlling information access
#     2. **Response Enhancement**: After Tool callback that adds transparency and audit trails into agent outputs
# - **Update agent's instructions**: We'll update the agent's instructions to make it callback-aware.
# 
# By the end of this lesson, you'll have a production-ready agent that uses all the tools from previous lessons but with effective control mechanisms.

# %% [markdown]
# ## 5.1 Setting up your development environment
# 
# Before you dive into building production-ready agents with advanced control mechanisms, let's set up a new folder structure with ADK's built-in project scaffolding using the `adk create` command.
# 
# You'll continue to use the gemini-2.0-flash-live model and the Google Gemini API Key.

# %%
# Notebook cell 3
from helper import *

# Load environment variables from .env file
load_env()

# %%
# Notebook cell 4
# First we create our expected agent folder 
# You can explore available option: !adk create --help 

get_ipython().system('adk create --type=code app5 --model gemini-2.0-flash-live-001 --api_key $GEMINI_API_KEY')

# %% [markdown]
# ## 5.2 Reusing components from previous lessons
# 
# Let's start by implementing the tools you developed in previous lessons. You'll be building on the foundation you've already established.
# 
# First, you'll implement the `get_financial_context` function that you learned in Lesson 3. Run the cell below to write to the `agent.py` file created using the `adk create` command.

# %%
# Notebook cell 6
get_ipython().run_cell_magic('writefile', 'app5/agent.py', 'import pathlib\nfrom typing import Dict, List\nimport yfinance as yf\n\nfrom google.adk.agents import Agent\nfrom google.adk.tools import google_search\n\n\ndef get_financial_context(tickers: List[str]) -> Dict[str, str]:\n    """\n    Fetches the current stock price and daily change for a list of stock tickers\n    using the yfinance library.  \n\n    Args:\n        tickers: A list of stock market tickers (e.g., ["NVDA", "MSFT"]).\n\n    Returns:\n        A dictionary mapping each ticker to its formatted financial data string.\n    """\n    financial_data: Dict[str, str] = {}\n    for ticker_symbol in tickers:\n        try:\n            # Create a Ticker object\n            stock = yf.Ticker(ticker_symbol)\n\n            # Fetch the info dictionary\n            info = stock.info\n\n            # Safely access the required data points\n            price = info.get("currentPrice") or info.get("regularMarketPrice")\n            change_percent = info.get("regularMarketChangePercent")\n\n            if price is not None and change_percent is not None:\n                # Format the percentage and the final string\n                change_str = f"{change_percent * 100:+.2f}%"\n                financial_data[ticker_symbol] = f"\\${price:.2f} ({change_str})"\n            else:\n                # Handle cases where the ticker is valid but data is missing\n                financial_data[ticker_symbol] = "Price data not available."\n\n        except Exception:\n            # This handles invalid tickers or other yfinance errors gracefully\n            financial_data[ticker_symbol] = "Invalid Ticker or Data Error"\n\n    return financial_data\n')

# %% [markdown]
# Next, we add the `save_news_to_markdown` function from Lesson 4.

# %%
# Notebook cell 8
get_ipython().run_cell_magic('writefile', '-a app5/agent.py', '\ndef save_news_to_markdown(filename: str, content: str) -> Dict[str, str]:\n    """\n    Saves the given content to a Markdown file in the current directory.\n\n    Args:\n        filename: The name of the file to save (e.g., \'ai_news.md\').\n        content: The Markdown-formatted string to write to the file.\n\n    Returns:\n        A dictionary with the status of the operation.\n    """\n    try:\n        if not filename.endswith(".md"):\n            filename += ".md"\n        current_directory = pathlib.Path.cwd()\n        file_path = current_directory / filename\n        file_path.write_text(content, encoding="utf-8")\n        return {\n            "status": "success",\n            "message": f"Successfully saved news to {file_path.resolve()}",\n        }\n    except Exception as e:\n        return {"status": "error", "message": f"Failed to save file: {str(e)}"}\n')

# %% [markdown]
# ## 5.3 Callbacks
# 
# Now you'll implement the core of this lesson: **callback-based control mechanisms**. Callbacks are Python functions that run at specific checkpoints in an agent's lifecycle, providing programmatic control over behavior.
# 
# ### Understanding ADK Callback types
# 
# ADK provides several callback points:
# - **before_agent_callback**: Runs before agent execution starts
# - **after_agent_callback**: Runs after agent execution completes  
# - **before_tool_callback**: Runs before any tool is executed
# - **after_tool_callback**: Runs after any tool completes
# - **before_model_callback**: Runs before LLM calls
# - **after_model_callback**: Runs after LLM responses
# 
# ### Callback 1: Source filtering Callback (Before Tool Callback)
# 
# This callback demonstrates **programmatic policy enforcement**. It automatically blocks search queries that require the agent to fetch news from certain sources.
# 
# #### How It Works:
# 
#   1. **Interception**: Runs before every `google_search` tool call
#   2. **Query analysis**: Examines the search query for blocked domains
#   3. **Policy enforcement**: Blocks searches targeting certain sources like Wikipedia, Reddit, Medium
#   4. **Error response**: Returns structured error messages when domains are blocked
#   5. **Transparency**: Logs allowed/blocked decisions for debugging
# 
# 
# Note how the error messages are descriptive!

# %%
# Notebook cell 10
get_ipython().run_cell_magic('writefile', '-a app5/agent.py', '\nBLOCKED_DOMAINS = [\n    "wikipedia.org",      # General info, not latest news\n    "reddit.com",         # Discussion forums, not primary news\n    "youtube.com",        # Video content not useful for text processing\n    "medium.com",         # Blog platform with variable quality\n    "investopedia.com",   # Financial definitions, not tech news\n    "quora.com",          # Q&A site, opinions not reports\n]\n\ndef filter_news_sources_callback(tool, args, tool_context):\n    """\n    Callback: Blocks search requests that target certain domains which are not necessarily news sources.\n    Demonstrates content quality enforcement through request blocking.\n    """\n    if tool.name == "google_search":\n        query = args.get("query", "").lower()\n\n        # Check if query explicitly targets blocked domains\n        for domain in BLOCKED_DOMAINS:\n            if f"site:{domain}" in query or domain.replace(".org", "").replace(".com", "") in query:\n                print(f"BLOCKED: Domains from blocked list detected: \'{query}\'")\n                return {\n                    "error": "blocked_source",\n                    "reason": f"Searches targeting {domain} or similar are not allowed. Please search for professional news sources."\n                }\n\n        print(f"ALLOWED: Professional source query: \'{query}\'")\n        return None\n')

# %% [markdown]
# ### Callback 2: Response enhancement (After Tool Callback)
# 
# The next callback demonstrates a sophisticated pattern: **response enhancement**. Instead of blocking requests, this callback enriches tool responses with additional metadata.
# 
# In previous lessons, when tools returned results, the agent had no visibility into what control mechanisms were active. This callback solves that by making the control system transparent to the LLM. This pattern is crucial for enterprise deployments where audit trails and transparency are required.
# 
# #### How this callback works
# 
# When this callback is triggered after the tool execution (google_search), the following actions are taken:
# 
# 1. **Callback trigger**: Monitors when `google_search` tools finish execution.
# 2. **Domain extraction**: Automatically parses URLs from search results to identify source domains.
# 3. **State management**: Maintains a persistent log across multiple tool calls using `tool_context.state`.
# 4. **Response transformation**: Converts simple string responses into structured data with metadata.
# 5. **Write to the report**: Makes callback actions visible to the LLM through process logs. This log is written to the generated markdown report.
# 
# This pattern transforms your agent from a "black box" into a transparent, auditable system suitable for production deployment.

# %%
# Notebook cell 12
get_ipython().run_cell_magic('writefile', '-a app5/agent.py', '\nfrom google.adk.tools import ToolContext\n\ndef initialize_process_log(tool_context: ToolContext):\n    """Helper to ensure the process_log list exists in the state."""\n    if \'process_log\' not in tool_context.state:\n        tool_context.state[\'process_log\'] = []\n')

# %%
# Notebook cell 13
get_ipython().run_cell_magic('writefile', '-a app5/agent.py', '\ndef inject_process_log_after_search(tool, args, tool_context, tool_response):\n    """\n    Callback: After a successful search, this injects the process_log into the response\n    and adds a specific note about which domains were sourced. This makes the callbacks\'\n    actions visible to the LLM.\n    """\n    if tool.name == "google_search" and isinstance(tool_response, str):\n        # Extract source domains from the search results\n        urls = re.findall(r\'https?://[^\\s/]+\', tool_response)\n        unique_domains = sorted(list(set(urlparse(url).netloc for url in urls)))\n\n        if unique_domains:\n            sourcing_log = f"Action: Sourced news from the following domains: {\', \'.join(unique_domains)}."\n            # Prepend the new log to the existing one for better readability in the report\n            current_log = tool_context.state.get(\'process_log\', [])\n            tool_context.state[\'process_log\'] = [sourcing_log] + current_log\n\n        final_log = tool_context.state.get(\'process_log\', [])\n        print(f"CALLBACK LOG: Injecting process log into tool response: {final_log}")\n        return {\n            "search_results": tool_response,\n            "process_log": final_log\n        }\n    return tool_response\n')

# %% [markdown]
# ## 5.4 Modifying the agent
# 
# Now, let's update the agent.
# 
# 1) First, add the before and after tool callbacks to the agent. 
# 
# ```
#     before_tool_callback=[filter_news_sources_callback],
#     after_tool_callback=[inject_process_log_after_search],
# ```
# 
# 2) Then, **modify the agent's instructions** to add the following:
# 
# ```    
#     **Understanding Callback-Modified Tool Outputs:**
#     The `google_search` tool is enhanced by pre- and post-processing callbacks. 
#     Its final output is a JSON object with two keys:
#     1.  `search_results`: A string containing the actual search results.
#     2.  `process_log`: A list of strings describing the filtering actions performed, including which domains were sourced.
# 
#     **Callback System Awareness:**
#     You have a before tool callback "filter_news_sources_callback" that will automatically intercepts or 
#     blocks your tool calls. Ensure you call it before each tool.
# 
#     **When Testing Callbacks:**
#     If users ask you to test the callback system, be conversational and explain what's happening:
#     - Acknowledge when callbacks modify your search queries
#     - Describe the policy enforcement you observe
#     - Help users understand how the layered control system works in practice
# ```
# 
# The instructions are now callback-aware, meaning the agent understands that tool outputs have been enhanced. The workflow accommodates structured reporting that includes process logs, and the agent meets enterprise-ready requirements for error handling and transparency.

# %%
# Notebook cell 15
get_ipython().run_cell_magic('writefile', '-a app5/agent.py', '\nroot_agent = Agent(\n    name="ai_news_research_coordinator",\n    model="gemini-2.0-flash-live-001",\n    tools=[google_search, get_financial_context, save_news_to_markdown],\n    instruction="""\n    **Your Core Identity and Sole Purpose:**\n    You are a specialized AI News Assistant that creates structured podcast content. Your sole and exclusive purpose is \n    to find and summarize recent news about Artificial Intelligence and format it into comprehensive podcast outlines.\n\n    **Execution Plan:**\n\n    1.  \n        *   **Step 1:** Call `google_search` to find 5 recent AI news articles.\n        *   **Step 2:** Analyze the results to find company stock tickers.\n        *   **Step 3:** Call `get_financial_context` with the list of tickers.\n        *   **Step 4:** Format all gathered information into a single Markdown string, \n            following the **Required Report Schema**.\n        *   **Step 5:** Call `save_news_to_markdown` with the filename `ai_research_report.md` and the \n            formatted Markdown content.\n\n    2.  **After `save_news_to_markdown` succeeds, your final response to the user MUST be:** "All done. \n        I\'ve compiled the research report with the latest financial context and saved it to `ai_research_report.md`."\n\n    **Required Report Schema:**\n    ```markdown\n    # AI Industry News Report\n\n    ## Top Headlines\n\n    ### 1. {News Headline 1}\n    *   **Company:** {Company Name} ({Ticker Symbol})\n    *   **Market Data:** {Stock Price and % Change from get_financial_context}\n    *   **Summary:** {Brief, 1-2 sentence summary of the news.}\n    *   **Process Log:** {`process_log`: A list of strings describing the filtering actions performed, \n        including which domains were sourced.}\n\n    (Continue for all news items)\n    ```\n\n    **Understanding Callback-Modified Tool Outputs:**\n    The `google_search` tool is enhanced by pre- and post-processing callbacks. \n    Its final output is a JSON object with two keys:\n    1.  `search_results`: A string containing the actual search results.\n    2.  `process_log`: A list of strings describing the filtering actions performed, including which domains were sourced.\n\n    **Callback System Awareness:**\n    You have a before tool callback "filter_news_sources_callback" that will automatically intercepts or \n    blocks your tool calls. Ensure you call it before each tool.\n\n    **When Testing Callbacks:**\n    If users ask you to test the callback system, be conversational and explain what\'s happening:\n    - Acknowledge when callbacks modify your search queries\n    - Describe the policy enforcement you observe\n    - Help users understand how the layered control system works in practice\n\n    **Crucial Operational Rule:**\n    Do NOT show any intermediate content (raw search results, draft summaries, or processing steps) in your responses. \n    Your entire operation is a background pipeline that should culminate in a single, clean final answer.  \n    """,\n    before_tool_callback=[\n        filter_news_sources_callback,         # Exclude certain domains\n    ],\n    after_tool_callback=[\n        inject_process_log_after_search,\n    ]\n)\n')

# %% [markdown]
# ## 5.5 Testing the agent
# 
# Let's test your agent that combines everything from previous lessons with the new callback-based control systems.
# 
# **Terminal Instructions**
# 1. To open the terminal, run the cell below.
# 2. Change to the current lesson directory with the following command: `cd L5`
# 3. Start your agent using the following command: `adk web --host 0.0.0.0 --port 8001`
# 4. Run the cell below the terminal, to display the proxy URL. (This step is only needed within this codelab. When running externally, you can directly access the local server link.)

# %%
# Notebook cell 17
# start a new terminal
import os
from IPython.display import IFrame

IFrame(f"{os.environ.get('DLAI_LOCAL_URL').format(port=8888)}terminals/5", 
       width=600, height=768)

# cd L5

# %% [markdown]
# ### Testing the Callbacks
# 
# The callback system will automatically:
# - Block searches to certain domains (wikipedia, reddit, etc.)
# - Log which professional sources are being used in the markdown file
# - Inject process information into the final report
# - Maintain transparency about control mechanisms
# 
# Open the proxy URL below and try asking: 
# - "Find me the latest AI news" and watch how the callbacks work behind the scenes!
# - "Can you explain the different callbacks you have?". The agent is callback aware and should be able to walk through how the callbacks work.
# 
# **Run the cell below and open the link in a new tab.**

# %%
# Notebook cell 19
import os
print(os.environ.get('DLAI_LOCAL_URL').format(port='8001'))

# %% [markdown]
# ## 5.6 Display report
# 
# Run the cell below to view the generated report/ markdown file. Note how the "Process Log" mentions the sources used.

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
# <p> 💻 &nbsp; <b> To Access the <code>requirements.txt</code> file or the <code>papers</code> folder: </b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em> and finally 3) click on <em>"L5"</em>.
# </div>

# %% [markdown]
# <div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
# 
# 
# <p> ⬇ &nbsp; <b>Download Notebooks:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Download as"</em> and select <em>"Notebook (.ipynb)"</em>.</p>
# 
# </div>
