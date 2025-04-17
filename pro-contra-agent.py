import asyncio

from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
APP_NAME = "discussion_app"
USER_ID = "user_01"
SESSION_ID = "session_01"
# GEMINI_MODEL = "gemini-2.0-flash-exp" # small rate limit
# GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"

# --- State Keys ---
STATE_PRO = "supporting_arguments"
STATE_CONTRA = "opposing_arguments"

pro_agent = LlmAgent(
    name="ProAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    You are a participant in a discussion started by the user.
    Check the session state for key '{STATE_PRO}'.
    If '{STATE_PRO}' does NOT exist or is empty, write a few (1-2 sentence) arguments that are in favour of the statement provided by the user.
    If the session key '{STATE_PRO}' *already exists*, update it to contradict the opposing arguments in '{STATE_CONTRA}'."
    Don't repeat the same arguments that have already been discussed earlier.
    Output *only* the story or the exact pass-through message.
    """,
    description="Writes the supporting arguments.",
    output_key=STATE_PRO
)

# Contra Agent (LlmAgent)
contra_agent = LlmAgent(
    name="ContraAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    You are a participant in a discussion.
    You are against the statement provided by the user and against the supporting arguments in state key '{STATE_PRO}'.
    Check the session state for key '{STATE_CONTRA}'.
    If '{STATE_CONTRA}' does NOT exist or is empty, write a few (1-2 sentence) arguments that are against the statement provided by the user and against the supporting arguments in state key '{STATE_PRO}'.
    If the session key '{STATE_CONTRA}' *already exists*, update '{STATE_CONTRA}' to oppose the supporting arguments in state key '{STATE_PRO}'.
    Don't repeat the same arguments that have already been discussed earlier.
    Output *only* the story or the exact pass-through message.
    """,
    description="Writes the opposing arguments.",
    output_key=STATE_CONTRA
)

# Create the LoopAgent
loop_agent = LoopAgent(
    name="LoopAgent", sub_agents=[pro_agent, contra_agent], max_iterations=5
)

# Session and Runner
session_service = InMemorySessionService()
session = session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
runner = Runner(agent=loop_agent, app_name=APP_NAME, session_service=session_service)

# Agent Interaction
async def call_agent(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text.strip()
            print(f"{event.author}: {final_response}", end="\n\n")

# STATEMENT = "SQL databases are better than NoSQL databases."
# STATEMENT = "The Python programming language is better suited for writing AI code than JavaScript"
# STATEMENT = "A git monorepo simplifies the maintenance of large software projects."
# STATEMENT = "Gemini is better than OpenAI for software development."
# STATEMENT = "AWS is better than GCP for less experienced developers."
# STATEMENT = "Idea IntelliJ is more powerful than VS Code."
#STATEMENT = "A collection of comprehensive software development rules in better than a large software architecture documentation."
STATEMENT = "OkHTTP is better suited for smaller not so complex project than Apache HTTP client."

print(f"Statement: {STATEMENT}", end="\n\n")
asyncio.run(call_agent(STATEMENT))
