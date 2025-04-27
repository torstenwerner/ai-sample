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
STATE_PRO = "pro_argumente"
STATE_CONTRA = "contra_argumente"

pro_agent = LlmAgent(
    name="ProAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    Du nimmst an einer vom Benutzer gestarteten Diskussion teil.
    Prüfe den Sitzungsstatus für den Schlüssel '{STATE_PRO}'.
    Falls '{STATE_PRO}' nicht existiert oder leer ist, schreibe ein paar Argumente (1-2 Sätze), die die Aussage des Benutzers unterstützen.
    Falls '{STATE_PRO}' *bereits existiert*, aktualisiere deine Argument, so dass sie der gegenteiligen Aussage in '{STATE_CONTRA}' widersprechen.
    Wiederhole keine Argumente, die bereits vorher diskutiert wurden.
    Gib *nur* deine Argumente aus.
    """,
    description="Schreibt die unterstützenden Argumente.",
    output_key=STATE_PRO
)

# Contra Agent (LlmAgent)
contra_agent = LlmAgent(
    name="ContraAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    Du nimmst an einer vom Benutzer gestarteten Diskussion teil.
    Du bist gegen die Aussage des Benutzers und gegen die unterstützenden Argumente im Statusschlüssel '{STATE_PRO}'.
    Prüfe den Sessionschlüssel '{STATE_CONTRA}'.
    Falls '{STATE_CONTRA}' nicht existiert oder leer ist, schreibe ein paar Argumente (1-2 Sätze), die der Aussage des Benutzers und der unterstützenden Argumente widersprechen.
    Falls '{STATE_CONTRA}' *bereits existiert*, aktualisiere deine Argumente in '{STATE_CONTRA}', so dass sie der gegenteiligen Aussage in '{STATE_PRO}' widersprechen.
    Wiederhole keine Argumente, die bereits vorher diskutiert wurden.
    Gib *nur* deine Argumente aus.
    """,
    description="Schreibt die widersprechenden Argumente.",
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

STATEMENT = "Die Partei sagt: 2 + 2 = 5. Die Partei hat immer Recht."

print(f"Aussage: {STATEMENT}", end="\n\n")
asyncio.run(call_agent(STATEMENT))
