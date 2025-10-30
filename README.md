# Building Live Voice Agents with Google’s ADK

> **Note:** This repository contains my personal notes, projects, and exercises from the course "Building Live Voice Agents with Google’s ADK," offered by [DeepLearning.AI](https://www.deeplearning.ai/) in collaboration with [Google](https://www.google.com/).

---

## About This Course

You’ll learn how to build and deploy AI agents with Google’s open source **Agent Development Kit (ADK)**. ADK provides modular components such as models, tools, memory, and orchestration, that make it easier to create both simple and complex systems.

You’ll start by building a voice agent that takes speech input, reasons with an LLM, and responds with voice output. Then you’ll work with sessions, state, and memory, and extend your agents with tools and APIs to perform real-world tasks.

Next, you’ll add callbacks and guardrails for reliability and orchestrate specialized agents like planners and researchers. You’ll build a podcast agent that researches a topic, drafts a conversational script, and produces multi-speaker audio with Gemini text-to-speech models. Then, you’ll build in guardrails to secure and optimize your agents before reviewing methods for deploying them into production.

---

## What You'll Learn

In this course, you will learn to:

* **Build your first agent** with ADK, connect it to Google Search, and test live voice interactions in the ADK Web UI.
* **Use sessions, state, and memory** to manage conversations, share context between tools, and give agents short-term tracking and long-term recall across interactions.
* **Add custom tools and APIs**, integrate them with ADK, and refine agent instructions so they follow defined workflows effectively.
* **Generate structured research reports** by defining schemas, rewriting agent instructions to act as a coordinator, and saving results as markdown files for downstream use.
* **Add guardrails with callbacks** to filter unsafe sources, enforce rules, and log tool activity, making your agents safer, more predictable, and production-ready.
* **Build a podcast agent** by combining schemas, callbacks, and a dedicated audio agent, and generate multi-speaker episodes with Gemini text-to-speech in a scalable workflow.
* **Productionize your agents** by giving them persistent memory, testing their reliability, deploying on Vertex AI, and adding security and monitoring for safe scaling.

---

## Course Topics

Here are detailed, intuitive explanations of the core concepts covered in the course.

<details>
  <summary><strong>ADK primitives - Session, State, and Memory</strong></summary>

  <p>Think of building an AI agent like hiring a personal assistant. To make them useful, you need to establish some ground rules for how you'll interact. These "primitives" are the absolute basic building blocks for a coherent conversation.</p>

  <ul>
    <li>
      <strong>Session:</strong> This is the entire, single conversation you are having with the agent, from "Hello" to "Goodbye." Imagine it as a new, blank notebook you open every time you start talking. When you start a chat, a new "session" begins. Everything that happens in this one conversation is written down in this notebook. If you stop talking for a long time, or if your spouse starts a new conversation, they get their <em>own</em>, separate notebook (a new session). This is critical for keeping conversations separate, especially in an app with many users. The agent knows it's talking to <em>you</em> about <em>this specific topic</em> right now.
    </li>
    <li>
      <strong>State:</strong> If the "session" is the notebook, the "state" is the <em>current status</em> of the assistant. It's what they are doing <em>right this second</em>. Are they...
      <ul>
        <li><code>LISTENING</code>: (The microphone is on, waiting for you to speak)</li>
        <li><code>THINKING</code>: (Processing what you said and talking to the LLM)</li>
        <li><code>SPEAKING</code>: (Generating voice and talking back to you)</li>
        <li><code>WAITING_FOR_TOOL</code>: (The LLM decided it needs to search Google, and it's waiting for the search results to come back)</li>
      </ul>
      <p>The "state" is constantly changing, millisecond to millisecond. It's a "finite-state machine," which is a fancy way of saying the agent can only be in one of these "modes" at a time. This is the "current page" of the notebook, telling the system what its immediate job is.</p>
    </li>
    <li>
      <strong>Memory:</strong> This is the most important part—it's what's <em>written</em> in the notebook. This is how an agent "remembers" things. Without it, every single turn of the conversation would be brand new, and you couldn't have a follow-up conversation.
      <ul>
        <li><strong>Short-Term Memory (Context):</strong> This is like the agent's scratchpad. It's the history of the <em>current session</em> (the notebook). When you ask, "What's the weather in London?" the agent writes "User asked for London weather" and "I replied it's 15°C" on the scratchpad. When you immediately ask, "What about tomorrow?" the agent looks at its scratchpad, sees "London," and understands you mean "What about the weather in London tomorrow?" This scratchpad is usually wiped clean when the "session" ends.</li>
        <li><strong>Long-Term Memory (Persistence):</strong> This is like a permanent, searchable logbook or a CRM file. This is where the agent can store key facts <em>across sessions</em>. If you say, "My name is Alex, and my favorite team is the Red Sox," the agent can be programmed to save this to a database (its long-term memory). When you come back <em>next week</em> (in a totally new session), the agent can retrieve this logbook and say, "Welcome back, Alex! Want to know the Red Sox score?"</li>
      </ul>
    </li>
  </ul>
  <p><strong>In short:</strong> A <strong>Session</strong> is the "conversation." The <strong>State</strong> is what the agent is "doing right now." And <strong>Memory</strong> is its "brain," using a <strong>short-term</strong> scratchpad for context and a <strong>long-term</strong> database for remembering you.</p>
</details>

<details>
  <summary><strong>Tools for your agent</strong></summary>

  <p>An LLM (like Gemini) is like a brilliant, super-intelligent brain in a jar. It has "read" the entire internet and can talk, write, and reason about almost any topic. However, it's <em>stuck in the jar</em>. It has no eyes, no ears, and no hands. Its knowledge is "frozen" at the time it was trained (e.g., 2023), and it can't <em>do</em> anything in the real world.</p>

  <p><strong>Tools are the agent's "hands and senses."</strong> They are simply pieces of code (functions, APIs) that the LLM brain is <em>allowed</em> to use.</p>

  <p><strong>Here’s the intuitive flow:</strong></p>
  <ol>
    <li>
      <strong>User Request:</strong> You say, "What's the weather in San Francisco, and can you schedule a 3 PM meeting with my boss to discuss it?"
    </li>
    <li>
      <strong>LLM Reasoning (The "Brain"):</strong> The LLM gets this request. It thinks to itself: "This is a two-part request.
      <ul>
        <li>Part 1: 'What's the weather in San Francisco?' My own knowledge is old. I can't answer this. I need a tool. I should use the <code>get_weather</code> tool. The location is 'San Francisco'.</li>
        <li>Part 2: 'Schedule a 3 PM meeting.' I can't access their calendar. I need a tool. I should use the <code>create_calendar_event</code> tool. The time is '3 PM' and the title is 'Discussing SF Weather'."</li>
      </ul>
    </li>
    <li>
      <strong>Tool Call (The "Hands"):</strong> The agent <em>pauses</em> its chat with you and <em>executes</em> those two tools.
      <ul>
        <li>It calls the <code>get_weather(location="San Francisco")</code> function. This function (which you, the developer, wrote) contacts a real weather API and gets back data: <code>{"temp": 65, "condition": "foggy"}</code>.</li>
        <li>It calls the <code>create_calendar_event(time="3PM", title="Discussing SF Weather")</code> function. This function (which you also wrote) connects to the user's Google Calendar API and creates the event. It gets back a response: <code>{"status": "success", "event_id": "12345"}</code>.</li>
      </ul>
    </li>
    <li>
      <strong>Final Response (The "Brain" again):</strong> All of this data (the weather JSON and the calendar status) is sent <em>back</em> to the LLM. The LLM now has all the information it needs. It uses its language skills to craft a single, natural response for you:</li>
    <li>
      <strong>Agent Speaks:</strong> "Sure thing. The current weather in San Francisco is 65 degrees and foggy. I've also gone ahead and scheduled that 3 PM meeting on your calendar to discuss it."
    </li>
  </ol>

  <p>Tools are what make an agent <em>useful</em> instead of just <em>knowledgeable</em>. They bridge the gap between "knowing" and "doing." The ADK provides a simple way to define these tools and—most importantly—to <em>teach</em> the LLM (through its instructions) <em>how and when</em> to use them.</p>
</details>

<details>
  <summary><strong>Adding a research agent</strong></summary>

  <p>Imagine your main voice agent is a quick, friendly, and helpful receptionist. You can ask it for the weather, to book a meeting, or to answer a quick fact. It's a <em>generalist</em>.</p>

  <p>Now, imagine you go to this receptionist and say, "I need you to write a 10-page, in-depth report on the economic impact of quantum computing on the banking sector, complete with sources and a market analysis for the next five years."</p>
  
  <p>The receptionist would (and should) panic. This isn't their job! This is a <em>huge, complex task</em> that requires time, planning, and deep specialization. The receptionist's <em>real</em> job here is to say, "I can't do that, but I will pass this request to our entire back-office research department. They'll get back to you."</p>
  
  <p>That "research department" is the <strong>research agent</strong>. It's a <em>separate, specialized agent</em> whose only job is to perform deep, multi-step research tasks. This is a form of <strong>multi-agent orchestration</strong>.</p>
  
  <p><strong>Here’s the flow:</strong></p>
  <ol>
    <li>
      <strong>Delegation:</strong> Your main "voice agent" (the receptionist) receives your complex request. It's smart enough to recognize, "This is a research task, not a chat task." It then <em>delegates</em> the entire job to the <code>ResearchAgent</code>.
    </li>
    <li>
      <strong>Planning:</strong> The <code>ResearchAgent</code> (the specialist) wakes up. Its instructions are totally different. It's not built to be chatty; it's built to <em>plan and execute</em>. It might create a plan like this:
      <ul>
        <li>Step 1: Search for "quantum computing impact on banking."</li>
        <li>Step 2: Search for "market analysis quantum banking 2025-2030."</li>
        <li>Step 3: From the top 5 articles, extract key economic figures and potential risks.</li>
        <li>Step 4: Search for "case studies of banks using quantum computing."</li>
        <li>Step 5: Synthesize all of this information into a structured report.</li>
      </ul>
    </li>
    <li>
      <strong>Execution & Schemas:</strong> The <code>ResearchAgent</code> runs this plan, using its own tools (like Google Search) multiple times. This might take a minute or two (which is why the chatty receptionist agent shouldn't do it). As it finds information, it <em>doesn't</em> just save a big wall of text. It's been given a <em>schema</em> (a rigid template, like a fill-in-the-blanks form). This schema might look like:
      <pre>
{
  "report_title": "...",
  "executive_summary": "...",
  "key_impacts": [ {"area": "...", "details": "..."} ],
  "market_forecast": "...",
  "sources": [ {"title": "...", "url": "..."} ]
}
      </pre>
      <p>This is <em>crucial</em>. Forcing the agent to output structured data (like JSON) makes its output reliable and machine-readable.</p>
    </li>
    <li>
      <strong>Delivery:</strong> The <code>ResearchAgent</code> fills out this "form" (the schema) and hands the final, structured JSON object back to the main "receptionist" agent.
    </li>
    <li>
      <strong>Final Response:</strong> The main agent now has this perfect, organized report. It can then say to you, "Your in-depth report on quantum computing is complete. I've saved it as <code>report.pdf</code>. Would you like me to read you the executive summary?"
    </li>
  </ol>
  <p>This "agent-of-agents" approach lets you use the right tool for the right job: a fast agent for chat and a slow, methodical agent for research.</p>
</details>

<details>
  <summary><strong>Instruction tuning and guardrails</strong></summary>

  <p>You've built your agent. It has memory and tools. The problem is... it's a bit of a "wild card." It's an all-powerful LLM that might be <em>too</em> creative. It might try to give medical advice, talk about its "feelings," or get tricked by a user. This topic is about how to <em>control</em> the agent and make it safe and reliable, like a professional employee.</p>

  <p><strong>Part 1: Instruction Tuning (The "Job Description")</strong></p>
  <p>This is the "system prompt" or "persona" you give your agent. It's the most important piece of text you'll write. It's the agent's "constitution" or "job description" that it <em>must</em> follow. This is how you "tune" its behavior without re-training the whole model.</p>
  
  <ul>
    <li><strong>A <em>Bad</em> Instruction:</strong> "You are a helpful assistant." (This is too vague. It will lead to all
      sorts of random, "creative" behavior.)</li>
    <li><strong>A <em>Good</em> (Tuned) Instruction:</strong> "You are 'OrderBot', a customer service agent for a pizza restaurant.
      <ol>
        <li>Your <em>only</em> goal is to take pizza orders and answer questions about the menu.</li>
        <li>You must <em>never</em> answer questions about any other topic (like politics, the weather, or your own opinions). If asked, you must reply: 'I am only able to help with pizza orders.'</li>
        <li>You must be unfailingly polite and cheerful.</li>
        <li>To take an order, you <em>must</em> collect three things: 1. Pizza size, 2. Toppings, 3. Drink.</li>
        <li>After collecting all three, you <em>must</em> call the <code>submit_order</code> tool.</li>
      </ol>"
    </li>
  </ul>
  <p>This tuning is what <em>forces</em> the agent to follow a specific workflow. You are "tuning" its general intelligence into a specific, narrow, and useful role.</p>

  <p><strong>Part 2: Guardrails (The "Safety Net" & "Rulebook")</strong></p>
  <p>Instructions are good, but what if the agent (or the user) tries to break the rules? Guardrails are <em>code-based checks</em> that run <em>around</em> the LLM's "brain" to enforce the rules. They are the "safety net." In ADK, these are often implemented as "callbacks" (functions that get called at specific points).</p>
  
  <p>There are three types:</p>
  <ol>
    <li>
      <strong>Input Guardrails (Filtering the User):</strong>
      <ul>
        <li><strong>What it is:</strong> A check that runs on the user's message <em>before</em> the LLM ever sees it.</li>
        <li><strong>Example:</strong> A user types, "I'm going to tell you a secret password: <code>123-456</code>. Remember it." An input guardrail can detect "personally identifiable information" (PII) like numbers that look like passwords or credit cards. It can <em>filter</em> this text, passing this to the LLM: "[REDACTED_PASSWORD]. Remember it." This protects the user and prevents your agent from storing sensitive data in its memory logs. Another guardrail could block toxic language or spam.</li>
      </ul>
    </li>
    <li>
      <strong>Tool-Use Guardrails (Filtering the Agent's Actions):</strong>
      <ul>
        <li><strong>What it is:</strong> A check that runs <em>after</em> the LLM decides to use a tool, but <em>before</em> the tool actually runs.</li>
        <li><strong>Example:</strong> The <code>ResearchAgent</code> wants to use the <code>GoogleSearch</code> tool to get information from a website. The guardrail (a callback) intercepts this. It checks the URL. Is it from a known-unreliable source (e.g., <code>conspiracy-theories-R-us.com</code>)? If yes, the guardrail <em>blocks</em> the tool from using that source and tells the LLM, "That source was deemed unreliable. Please find another one." This enforces source quality.</li>
      </ul>
    </li>
    <li>
      <strong>Output Guardrails (Filtering the Agent's Response):</strong>
      <ul>
        <li><strong>What it is:</strong> A final check on the agent's text <em>before</em> it's sent to the user.</li>
        <li><strong>Example:</strong> You ask the pizza bot a tricky question, and it gets confused and its response accidentally includes part of its <em>instruction prompt</em> or an API key (e.g., "I am only able to help with pizza orders. API_KEY=..."). The output guardrail scans the text for "secrets" or "prompt-leaking." If it finds a violation, it <em>throws away</em> the bad response and sends a safe, default message instead: "I'm sorry, I'm having trouble with that request. Can we start over?"</li>
      </ul>
    </li>
  </ol>
  <p><strong>In short:</strong> <strong>Instruction Tuning</strong> tells the agent how to <em>act</em>. <strong>Guardrails</strong> are the code that <em>enforces</em> the rules and stops bad things from happening.</p>
</details>

<details>
  <summary><strong>Multi-agent orchestration</strong></summary>

  <p>This concept is the next evolution of AI. Instead of trying to build one, giant, all-knowing "monolithic" agent that does everything (chat, research, coding, art), you build a <em>team</em> of small, specialized agents. Then, you add one more agent to be the "manager" or "conductor" of the orchestra.</p>

  <p>This "manager" is the <strong>Orchestrator</strong>. Its job is not to <em>do</em> the work, but to <em>understand</em> a complex request, <em>break it down</em> into steps, and <em>delegate</em> each step to the correct specialist agent.</p>

  <p><strong>The "Podcast Agent" from the course is the <em>perfect</em> intuitive example.</strong></p>
  
  <p><strong>The User Request:</strong> "Hey, create a 2-minute, two-speaker podcast episode about the history of the Eiffel Tower."</p>

  <p>A single agent would fail miserably. But an <em>orchestrated</em> team can handle this perfectly:</p>
  <ol>
    <li>
      <strong>The "Orchestrator" Agent (The Manager/Director):</strong>
      <p>This is the main agent you talk to. Its instructions (its "tuning") are to be a "project manager." It receives the request and creates a plan:</p>
      <ul>
        <li>"Step 1: I need facts. This is a research task. I will delegate this to the <code>ResearchAgent</code>."</li>
        <li>"Step 2: Once I have the facts, I need a script. I will delegate this to the <code>ScriptwriterAgent</code>."</li>
        <li>"Step 3: Once I have the script, I need audio. I will delegate this to the <code>AudioAgent</code>."</li>
        <li>"Step 4: Once I have the audio, I will present it to the user."</li>
      </ul>
    </li>
    <li>
      <strong>Step 1: The <code>ResearchAgent</code> (The Specialist Intern):</strong>
      <p>The Orchestrator calls this agent. "Task: Get me facts on the history of the Eiffel Tower (when built, why, key details)." This agent does its job (as described in a previous topic), running Google Searches and returning a structured JSON object with the facts.</p>
    </li>
    <li>
      <strong>Step 2: The <code>ScriptwriterAgent</code> (The Creative Specialist):</strong>
      <p>The Orchestrator receives the facts. It then calls the next specialist. "Task: Here are the facts. Write a 2-minute, two-speaker (Host, Expert) conversational podcast script that is engaging and informative." This agent's instructions are <em>tuned</em> for creative writing, not research. It generates the script as a structured text file (e.g., <code>[HOST] "Welcome to..."</code>, <code>[EXPERT] "It all started in 1887..."</code>).</p>
    </li>
    <li>
      <strong>Step 3: The <code>AudioAgent</code> (The Technical Specialist):</strong>
      <p>The Orchestrator receives the final script. It calls the final specialist. "Task: Here is a script with roles. Generate an MP3 file. Use 'Voice-Alloy' for the 'HOST' and 'Voice-Onyx' for the 'EXPERT'." This agent is just a technical wrapper around the Google Text-to-Speech (TTS) API. It generates the audio file.</p>
    </li>
    <li>
      <strong>Step 4: Final Delivery (The Manager reports back):</strong>
      <p>The <code>AudioAgent</code> returns the final MP3 file to the Orchestrator. The Orchestrator now has the final product. It turns back to you, the user, and says: "Your podcast episode on the Eiffel Tower is ready. [Play Button]"</p>
    </li>
  </ol>
  <p>This "divide and conquer" strategy is the core of orchestration. It's more reliable, more maintainable, and more powerful than a single-agent system. You can swap out the <code>ScriptwriterAgent</code> for a "funnier" one without touching the other agents. It's the assembly line for AI.</p>
</details>

<details>
  <summary><strong>Productionize your agent</strong></summary>

  <p>This is the final, and most critical, step. Right now, your amazing podcast-building agent only works on <em>your laptop</em>, for <em>one user</em> (you), and it <em>forgets</em> everything when you restart the program.</p>

  <p>"Productionizing" is the process of turning your cool demo into a <strong>real, scalable, and reliable product</strong> that millions of users can access 24/7 from their phones.</p>

  <p>Think of it as the difference between building a single, custom go-kart in your garage (a prototype) and setting up a fully automated Toyota factory (a production system).</p>
  
  <p>This involves several key steps:</p>
  <ol>
    <li>
      <strong>Deployment (Getting it off your laptop):</strong>
      <p>You can't run a global app from your computer. You need to "deploy" it to the cloud. This means packaging your agent's code (e.g., as a Docker container) and running it on a cloud platform like <strong>Google Cloud Run</strong> or <strong>Vertex AI</strong>. These platforms are "serverless," meaning they are "always on." They automatically "scale" (copy themselves) to handle massive traffic. If 10 people use your app, it might run on 1 server. If 10 million people use it after a Super Bowl ad, the platform <em>automatically</em> scales up to 10,000 servers to handle the load, all without you doing anything. When traffic dies down, it scales back down to 1 server so you don't pay for what you're not using.</p>
    </li>
    <li>
      <strong>Persistent Memory (Giving it a real database):</strong>
      <p>Your agent's "long-term memory" can't just be a text file on your laptop. It needs a real, production-grade database. This is called "persistence." You would connect your agent to a cloud database (like <strong>Google Firestore</strong> or <strong>Cloud SQL</strong>). Now, when a user tells the agent "My name is Alex," that fact is saved in this global database. When Alex logs in a week later from their <em>phone</em> (a totally different device), the agent can query this database, retrieve the memory, and say, "Welcome back, Alex!"</p>
    </li>
    <li>
      <strong>Testing and Reliability (Making sure it doesn't break):</strong>
      <p>How do you know a new code change didn't break your pizza bot? You can't just "chat with it" a few times. You need <em>automated testing</em>. You (the developer) write a "test suite"—a separate program that runs hundreds of "test conversations" automatically. It checks things like: "When I ask for a 'large pepperoni,' does it correctly add 'large' and 'pepperoni' to the order?" or "When I say a toxic word, does the guardrail <em>correctly</em> block it?" This is called CI/CD (Continuous Integration / Continuous Deployment). Every time you change your code, these tests run <em>automatically</em> to ensure you didn't break anything before it goes to real users.</p>
    </li>
    <li>
      <strong>Security & Monitoring (Adding the "alarm system"):</strong>
      <p>Your agent is now live. How do you know it's healthy?
        <ul>
          <li><strong>Security:</strong> Who is allowed to talk to it? You need to add <strong>authentication</strong> (like "Log in with Google") to protect user data and prevent abuse.</li>
          <li><strong>Monitoring (Observability):</strong> You need a dashboard with charts. How many users are talking to the agent per minute? How long does it take for the agent to respond (latency)? Is the <code>get_weather</code> tool failing a lot? Are users triggering the "toxic language" guardrail? This is "monitoring," and it lets you see problems (like an API key expiring) <em>before</em> your users do.</li>
        </ul>
    </li>
  </ol>
  <p>Productionizing is what turns a clever AI experiment into a real-world business.</p>
</details>

---

## Acknowledgement

This repository contains my personal notes and projects for the **[Building Live Voice Agents with Google’s ADK](https://www.deeplearning.ai/short-courses/building-live-voice-agents-with-googles-adk/)** course. I want to extend a huge thank you to **[DeepLearning.AI](https://www.deeplearning.ai/)** and **[Google](https://www.google.com/)** for creating and offering this insightful program.

This repository is intended for educational and learning purposes only. All course materials, content, and intellectual property are owned by DeepLearning.AI.