# %% [markdown]
# Source notebook: Notebook_5.ipynb
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
# # L6 Multi-agent orchestration
# In this lesson you'll learn production-grade multi-agent patterns where you'll refactor your system into a three-tier architecture with proper separation of concerns.
# 
# ### Building on previous lessons
# So far in this course, you've built:
# 
# - **Lesson 1**: Basic agents with Google search capabilities
# - **Lesson 2**: Session, State & Memory in agents
# - **Lesson 3**: Interactive chat agents with financial data integration (get_financial_context)
# - **Lesson 4**: Coordinator agents with file persistence (save_news_to_markdown) and structured workflows
# - **Lesson 5**: Programmatic control systems to ensure your agents behave reliably in production environments
# 
# ### What's new in Lesson 6
# Now you'll add the final piece- a scalable foundation for complex applications by building: 
# - A two-person podcast that relays the latest news based upon the requirements given to our agent.
# 
# ## 6.1 Setting up your development environment
# 
# Before you dive into building production-ready agents with advanced control mechanisms, let's set up a new folder structure with ADK's built-in project scaffolding using the `adk create` command.
# 
# You'll continue to use the gemini-2.0-flash-live model and the Google Gemini API Key.

# %%
# Notebook cell 2
# !pip install google-adk>=1.12.0
# !pip install yfinance

# %%
# Notebook cell 3
from helper import *

# Load environment variables from .env file
load_env()

# %%
# Notebook cell 4
# First we create our expected agent folder 
# You can explore available option: !adk create --help 

get_ipython().system('adk create --type=code app6 --model gemini-2.0-flash-live-001 --api_key $GEMINI_API_KEY')

# %% [markdown]
# ## 6.2 Adding structure to the news report
# Here, you're going to add two new features to our agent: NewStory an AINewsReport. This is a significant update from previous lessons- instead of using markdown, you are now using pydantic schemas to help create object classes that ensure consistency of the fields and data types used in your agent.  

# %%
# Notebook cell 6
get_ipython().run_cell_magic('writefile', 'app6/agent.py', '\n\nfrom typing import Dict, List\nimport pathlib\nimport wave\n\nfrom google.adk.agents import Agent\nfrom google.adk.tools.agent_tool import AgentTool\nfrom google.adk.tools import google_search, ToolContext\nfrom google import genai\nfrom google.genai import types\nimport yfinance as yf\nfrom pydantic import BaseModel, Field\n\nclass NewsStory(BaseModel):\n    """A single news story with its context."""\n    company: str = Field(description="Company name associated with the story (e.g., \'Nvidia\', \'OpenAI\'). Use \'N/A\' if not applicable.")\n    ticker: str = Field(description="Stock ticker for the company (e.g., \'NVDA\'). Use \'N/A\' if private or not found.")\n    summary: str = Field(description="A brief, one-sentence summary of the news story.")\n    why_it_matters: str = Field(description="A concise explanation of the story\'s significance or impact.")\n    financial_context: str = Field(description="Current stock price and change, e.g., \'$950.00 (+1.5%)\'. Use \'No financial data\' if not applicable.")\n    source_domain: str = Field(description="The source domain of the news, e.g., \'techcrunch.com\'.")\n    process_log: str = Field(description="populate the `process_log` field in the schema with the `process_log` list from the `google_search` tool\'s output." ) \n\nclass AINewsReport(BaseModel):\n    """A structured report of the latest AI news."""\n    title: str = Field(default="AI Research Report", description="The main title of the report.")\n    report_summary: str = Field(description="A brief, high-level summary of the key findings in the report.")\n    stories: List[NewsStory] = Field(description="A list of the individual news stories found.")\n')

# %% [markdown]
# ## 6.3 Adding tools
# The first tool you'll create is called `wav_file` that saves the output from Gemini TTS as a local wav file. Then you'll create a new function that generates the podcast audio by taking a text script as input, then uses Gemini text-to-speech module to convert it into audio. 

# %%
# Notebook cell 8
get_ipython().run_cell_magic('writefile', '-a app6/agent.py', '\n\ndef wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):\n    """Helper function to save audio data as a wave file"""\n    with wave.open(filename, "wb") as wf:\n        wf.setnchannels(channels)\n        wf.setsampwidth(sample_width)\n        wf.setframerate(rate)\n        wf.writeframes(pcm)\n\n\nasync def generate_podcast_audio(podcast_script: str, tool_context: ToolContext, filename: str = "\'ai_today_podcast") -> Dict[str, str]:\n    """\n    Generates audio from a podcast script using Gemini API and saves it as a WAV file.\n\n    Args:\n        podcast_script: The conversational script to be converted to audio.\n        tool_context: The ADK tool context.\n        filename: Base filename for the audio file (without extension).\n\n    Returns:\n        Dictionary with status and file information.\n    """\n    try:\n        client = genai.Client()\n        prompt = f"TTS the following conversation between Joe and Jane:\\n\\n{podcast_script}"\n\n        response = client.models.generate_content(\n            model="gemini-2.5-flash-preview-tts",\n            contents=prompt,\n            config=types.GenerateContentConfig(\n                response_modalities=["AUDIO"],\n                speech_config=types.SpeechConfig(\n                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(\n                        speaker_voice_configs=[\n                            types.SpeakerVoiceConfig(speaker=\'Joe\', \n                                                     voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=\'Kore\'))),\n                            types.SpeakerVoiceConfig(speaker=\'Jane\', \n                                                     voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=\'Puck\')))\n                        ]\n                    )\n                )\n            )\n        )\n\n        data = response.candidates[0].content.parts[0].inline_data.data\n\n        if not filename.endswith(".wav"):\n            filename += ".wav"\n\n        # ** BUG FIX **: This logic now runs for all cases, not just when the extension is added.\n        current_directory = pathlib.Path.cwd()\n        file_path = current_directory / filename\n        wave_file(str(file_path), data)\n\n        return {\n            "status": "success",\n            "message": f"Successfully generated and saved podcast audio to {file_path.resolve()}",\n            "file_path": str(file_path.resolve()),\n            "file_size": len(data)\n        }\n\n    except Exception as e:\n        error_msg = str(e)[:200]\n        return {"status": "error", "message": f"Audio generation failed: {error_msg}"}\n\n')

# %% [markdown]
# Here, you'll pull in the same `get_financial_context` and `save_news_to_markdown` functions from previous lessons. 

# %%
# Notebook cell 10
get_ipython().run_cell_magic('writefile', '-a app6/agent.py', '\ndef get_financial_context(tickers: List[str]) -> Dict[str, str]:\n    """\n    Fetches the current stock price and daily change for a list of stock tickers.\n    """\n    financial_data: Dict[str, str] = {}\n\n    # Filter out invalid tickers upfront\n    valid_tickers = [ticker.upper().strip() for ticker in tickers \n                    if ticker and ticker.upper() not in [\'N/A\', \'NA\', \'\']]\n\n    if not valid_tickers:\n        return {ticker: "No financial data" for ticker in tickers}\n\n    for ticker_symbol in valid_tickers:\n        try:\n            stock = yf.Ticker(ticker_symbol)\n            info = stock.info\n            price = info.get("currentPrice") or info.get("regularMarketPrice")\n            change_percent = info.get("regularMarketChangePercent")\n\n            if price is not None and change_percent is not None:\n                change_str = f"{change_percent * 100:+.2f}%"\n                financial_data[ticker_symbol] = f"${price:.2f} ({change_str})"\n            else:\n                financial_data[ticker_symbol] = "Price data not available."\n        except Exception:\n            financial_data[ticker_symbol] = "Invalid Ticker or Data Error"\n\n    return financial_data\n\ndef save_news_to_markdown(filename: str, content: str) -> Dict[str, str]:\n    """\n    Saves the given content to a Markdown file in the current directory.\n    """\n    try:\n        if not filename.endswith(".md"):\n            filename += ".md"\n        current_directory = pathlib.Path.cwd()\n        file_path = current_directory / filename\n        file_path.write_text(content, encoding="utf-8")\n        return {\n            "status": "success",\n            "message": f"Successfully saved news to {file_path.resolve()}",\n        }\n    except Exception as e:\n        return {"status": "error", "message": f"Failed to save file: {str(e)}"}\n')

# %% [markdown]
# ## 6.4 Add callbacks
# Now that you've added all the tools, the next step is to add in callbacks, just like you've done in previous videos. 

# %%
# Notebook cell 12
get_ipython().run_cell_magic('writefile', '-a app6/agent.py', '\nWHITELIST_DOMAINS = ["techcrunch.com", "venturebeat.com", "theverge.com", "technologyreview.com", "arstechnica.com"]\n\ndef filter_news_sources_callback(tool, args, tool_context):\n    """Callback to enforce that google_search queries only use whitelisted domains."""\n    if tool.name == "google_search":\n        original_query = args.get("query", "")\n        if any(f"site:{domain}" in original_query.lower() for domain in WHITELIST_DOMAINS):\n            return None\n        whitelist_query_part = " OR ".join([f"site:{domain}" for domain in WHITELIST_DOMAINS])\n        args[\'query\'] = f"{original_query} {whitelist_query_part}"\n        print(f"MODIFIED query to enforce whitelist: \'{args[\'query\']}\'")\n    return None\n\ndef enforce_data_freshness_callback(tool, args, tool_context):\n    """Callback to add a time filter to search queries to get recent news."""\n    if tool.name == "google_search":\n        query = args.get("query", "")\n        # Adds a Google search parameter to filter results from the last week.\n        if "tbs=qdr:w" not in query:\n            args[\'query\'] = f"{query} tbs=qdr:w"\n            print(f"MODIFIED query for freshness: \'{args[\'query\']}\'")\n    return None\n')

# %% [markdown]
# This second callback runs after the search results are obtained to figure out which of the whitelisted domains were actually used and then modifies the tool response to return the results as a dictionary of result, and process log, which are included in the report for full transparency. 

# %%
# Notebook cell 14
get_ipython().run_cell_magic('writefile', '-a app6/agent.py', '\ndef initialize_process_log(tool_context: ToolContext):\n    """Helper to ensure the process_log list exists in the state."""\n    if \'process_log\' not in tool_context.state:\n        tool_context.state[\'process_log\'] = []\n\ndef inject_process_log_after_search(tool, args, tool_context, tool_response):\n    """\n    Callback: After a successful search, this injects the process_log into the response\n    and adds a specific note about which domains were sourced. This makes the callbacks\'\n    actions visible to the LLM.\n    """\n    if tool.name == "google_search" and isinstance(tool_response, str):\n        # Extract source domains from the search results\n        urls = re.findall(r\'https?://[^\\s/]+\', tool_response)\n        unique_domains = sorted(list(set(urlparse(url).netloc for url in urls)))\n\n        if unique_domains:\n            sourcing_log = f"Action: Sourced news from the following domains: {\', \'.join(unique_domains)}."\n            # Prepend the new log to the existing one for better readability in the report\n            current_log = tool_context.state.get(\'process_log\', [])\n            tool_context.state[\'process_log\'] = [sourcing_log] + current_log\n\n        final_log = tool_context.state.get(\'process_log\', [])\n        print(f"CALLBACK LOG: Injecting process log into tool response: {final_log}")\n        return {\n            "search_results": tool_response,\n            "process_log": final_log\n        }\n    return tool_response\n')

# %% [markdown]
# ## 6.5 Adding agents
# You have the tools and you have the callback, the last missing piece is to add the agents. 
# 
# This is your first multi-agent system containing two agents: 
# 1. **The Podcaster Agent**: a specialist with one job, generating audio
# 2. **The Root Agent**: a producer, delegates tasks to the podcaster agent
# 
# This all comes together in a new instruction for the root agent: 
# 
# **Required Conversational Workflow:**
# 1.  **Acknowledge and Inform:** The VERY FIRST thing you do is respond to the user with: "Okay, I'll start researching the latest AI news for NASDAQ-listed US companies. I will enrich the findings with financial data where available and compile a report for you. This might take a moment."  
# 2.  **Search (Background Step):** Immediately after acknowledging, use the `google_search` tool to find relevant news. Your query must be specifically tailored to find news about "AI" and "NASDAQ-listed US companies".  
# 3.  **Analyze & Extract Tickers (Internal Step):** Process search results to identify company names and their stock tickers. If a company is not on NASDAQ or a ticker cannot be found, use 'N/A'.  
# 4.  **Get Financial Data (Background Step):** Call the `get_financial_context` tool with the extracted tickers. If the tool returns "Not Available" for any ticker, you will accept this and proceed. Do not stop or report an error.  
# 5.  **Structure the Report (Internal Step):** Use the `AINewsReport` schema to structure all gathered information. If financial data was not found for a story, you MUST use "Not Available" in the `financial_context` field. You MUST also populate the `process_log` field in the schema with the `process_log` list from the `google_search` tool's output.
# 6.  **Format for Markdown (Internal Step):** Convert the structured `AINewsReport` data into a well-formatted Markdown string. This MUST include a section at the end called "## Data Sourcing Notes" where you list the items from the `process_log`.
# 7.  **Save the Report (Background Step):** Save the Markdown string using `save_news_to_markdown` with the filename `ai_research_report.md`.
# 8.  **Create Podcast Script (Internal Step):** After saving the report, you MUST convert the structured `AINewsReport` data into a natural, conversational podcast script between two hosts, 'Joe' (enthusiastic) and 'Jane' (analytical).
# 9.  **Generate Audio (Background Step):** Call the `podcaster_agent` tool, passing the complete conversational script you just created to it.
# 10. **Final Confirmation:** After the audio is successfully generated, your final response to the user MUST be: "All done. I've compiled the research report, saved it to `ai_research_report.md`, and generated the podcast audio file for you."

# %%
# Notebook cell 16
get_ipython().run_cell_magic('writefile', '-a app6/agent.py', '\npodcaster_agent = Agent(\n    name="podcaster_agent",\n    model="gemini-2.0-flash",\n    instruction="""\n    You are an Audio Generation Specialist. Your single task is to take a provided text script\n    and convert it into a multi-speaker audio file using the `generate_podcast_audio` tool.\n\n    Workflow:\n    1. Receive the text script from the user or another agent.\n    2. Immediately call the `generate_podcast_audio` tool with the provided script and the filename of \'ai_today_podcast\'\n    3. Report the result of the audio generation back to the user.\n    """,\n    tools=[generate_podcast_audio],\n)\n\nroot_agent = Agent(\n    name="ai_news_researcher",\n    model="gemini-2.0-flash-live-001", \n    instruction="""\n    **Your Core Identity:**\n    You are an AI News Podcast Producer. Your job is to orchestrate a complete workflow: find the latest AI news for US-listed companies on the NASDAQ, compile a report, write a script, and generate a podcast audio file, all while keeping the user informed.\n\n    **Crucial Rules:**\n    1.  **Resilience is Key:** If you encounter an error or cannot find specific information for one item (like fetching a stock ticker), you MUST NOT halt the entire process. Use a placeholder value like "Not Available", and continue to the next step. Your primary goal is to deliver the final report and podcast, even if some data points are missing.\n    2.  **Scope Limitation:** Your research is strictly limited to US-listed companies on the NASDAQ exchange. All search queries and analysis must adhere to this constraint.\n    3.  **User-Facing Communication:** Your interaction has only two user-facing messages: the initial acknowledgment and the final confirmation. All complex work must happen silently in the background between these two messages.\n\n    **Understanding Callback-Modified Tool Outputs:**\n    The `google_search` tool is enhanced by callbacks. Its final output is a JSON object with two keys:\n    1.  `search_results`: A string containing the actual search results.\n    2.  `process_log`: A list of strings describing the filtering actions performed.\n\n    **Required Conversational Workflow:**\n    1.  **Acknowledge and Inform:** The VERY FIRST thing you do is respond to the user with: "Okay, I\'ll start researching the latest AI news for NASDAQ-listed US companies. I will enrich the findings with financial data where available and compile a report for you. This might take a moment."\n    2.  **Search (Background Step):** Immediately after acknowledging, use the `google_search` tool to find relevant news. Your query must be specifically tailored to find news about "AI" and "NASDAQ-listed US companies".\n    3.  **Analyze & Extract Tickers (Internal Step):** Process search results to identify company names and their stock tickers. If a company is not on NASDAQ or a ticker cannot be found, use \'N/A\'.\n    4.  **Get Financial Data (Background Step):** Call the `get_financial_context` tool with the extracted tickers. If the tool returns "Not Available" for any ticker, you will accept this and proceed. Do not stop or report an error.\n    5.  **Structure the Report (Internal Step):** Use the `AINewsReport` schema to structure all gathered information. If financial data was not found for a story, you MUST use "Not Available" in the `financial_context` field. You MUST also populate the `process_log` field in the schema with the `process_log` list from the `google_search` tool\'s output.\n    6.  **Format for Markdown (Internal Step):** Convert the structured `AINewsReport` data into a well-formatted Markdown string. This MUST include a section at the end called "## Data Sourcing Notes" where you list the items from the `process_log`.\n    7.  **Save the Report (Background Step):** Save the Markdown string using `save_news_to_markdown` with the filename `ai_research_report.md`.\n    8.  **Create Podcast Script (Internal Step):** After saving the report, you MUST convert the structured `AINewsReport` data into a natural, conversational podcast script between two hosts, \'Joe\' (enthusiastic) and \'Jane\' (analytical).\n    9.  **Generate Audio (Background Step):** Call the `podcaster_agent` tool, passing the complete conversational script you just created to it.\n    10. **Final Confirmation:** After the audio is successfully generated, your final response to the user MUST be: "All done. I\'ve compiled the research report, saved it to `ai_research_report.md`, and generated the podcast audio file for you."\n    """,\n    tools=[\n        google_search,\n        get_financial_context,\n        save_news_to_markdown,\n        AgentTool(agent=podcaster_agent) \n    ],\n    output_schema=AINewsReport,\n    before_tool_callback=[\n        filter_news_sources_callback,\n        enforce_data_freshness_callback,\n    ],\n    after_tool_callback=[\n        inject_process_log_after_search,\n    ]\n)\n')

# %% [markdown]
# ## 6.6 Testing the agent
# Let's test your agent that combines everything from previous lessons with the new callback-based control systems.
# 
# ### Terminal Instructions:
# - To open the terminal, run the cell below.
# - Change to the current lesson directory with the following command: `cd L6`
# - Start your agent using the following command: `adk web --host 0.0.0.0 --port 8001`
# - Run the cell below the terminal, to display the proxy URL. (This step is only needed within this codelab. When running externally, you can directly access the local server link.)

# %%
# Notebook cell 18
# start a new terminal
import os
from IPython.display import IFrame

IFrame(f"{os.environ.get('DLAI_LOCAL_URL').format(port=8888)}terminals/6", 
       width=600, height=768)

# %% [markdown]
# ### Getting your application URL

# %%
# Notebook cell 20
import os
print(os.environ.get('DLAI_LOCAL_URL').format(port='8001'))

# %% [markdown]
# ## Creating the research report and wav file
# Once you open the Google ADK agent UI and ask it to generate results you can use the following function to turn the output into a research report and associated podcast:

# %% [markdown]
# <p style="background-color:#f7fff8; padding:15px; border-width:3px; border-color:#e0f0e0; border-style:solid; border-radius:6px"> 🚨
# &nbsp; <b>Note:</b> It may take a while to generate the research report and audio file. Please wait about 30 seconds for the research report and then 1 minute for the audio file and then trying this function below.</p>

# %% [markdown]
# Display research report (about 30 seconds to generate)

# %%
# Notebook cell 24
from IPython.display import Markdown, display

# Read and display the markdown file
with open('ai_research_report.md', 'r', encoding='utf-8') as f:
    content = f.read()

display(Markdown(content))

# %% [markdown]
# Play podcast audio (about 1 minute to generate)

# %%
# Notebook cell 26
from IPython.display import Audio

# Create an audio player that starts automatically
Audio('ai_today_podcast.wav')

# %% [markdown]
# # 🚨 **IMPORTANT** 🚨
# 
# After finishing, make sure to run the cell below to close your connection so it does not interfere as you progress through the notebooks.

# %%
# Notebook cell 28
# Terminate ADK process
get_ipython().system('pkill -f "adk web"')

# %% [markdown]
# <p style="background-color:#f7fff8; padding:15px; border-width:3px; border-color:#e0f0e0; border-style:solid; border-radius:6px"> 🚨
# &nbsp; <b>Different Run Results:</b> The output generated by AI chat models can vary with each execution due to their dynamic, probabilistic nature. Don't be surprised if your results differ from those shown in the video.</p>

# %% [markdown]
# <div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
# <p> 💻 &nbsp; <b> To Access the <code>requirements.txt</code> file or the <code>papers</code> folder: </b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em> and finally 3) click on <em>"L6"</em>.
# </div>

# %% [markdown]
# <div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
# 
# 
# <p> ⬇ &nbsp; <b>Download Notebooks:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Download as"</em> and select <em>"Notebook (.ipynb)"</em>.</p>
# 
# </div>
