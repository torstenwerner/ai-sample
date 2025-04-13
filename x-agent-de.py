import asyncio

from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
APP_NAME = "doc_writing_app"
USER_ID = "dev_user_01"
SESSION_ID = "session_01"
# GEMINI_MODEL = "gemini-2.0-flash-exp" # small rate limit
GEMINI_MODEL = "gemini-2.0-flash"

# --- State Keys ---
STATE_INITIAL_TOPIC = "Friedrich Merz kann ein europäischer Anti-Trump werden"
STATE_CURRENT_DOC = "current_document"
STATE_CRITICISM = "criticism"

writer_agent = LlmAgent(
    name="WriterAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    Du bist eine KI für kreatives Schreiben von Kommentaren auf X.com.
    Überprüfe den Sitzungsstatus für '{STATE_CURRENT_DOC}'.
    Wenn '{STATE_CURRENT_DOC}' NICHT existiert oder leer ist, schreibe einen Kommentar für X.com, der sowohl kritisch als auch subtil ironisch und spöttisch auf das Thema '{STATE_INITIAL_TOPIC}' eingeht.
    Wenn '{STATE_CURRENT_DOC}' bereits existiert und '{STATE_CRITICISM}', verfeinere '{STATE_CURRENT_DOC}' gemäß den Kommentaren in '{STATE_CRITICISM}'.
    Gib *nur* die Geschichte oder die genaue Durchgangsnachricht aus.
    """,
    description="Schreibt oder verbessert einen Kommentarentwurf.",
    output_key=STATE_CURRENT_DOC  # Saves output to state
)


def stop_tool(tool_context: ToolContext) -> None:
    """Wird immer dann aufgerufen, wenn es keine Kritik gibt."""
    # print("Stopping tool called.")
    tool_context.actions.escalate = True

# escalation_tool = FunctionTool(func=stop_tool)

# Critic Agent (LlmAgent)
critic_agent = LlmAgent(
    name="CriticAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    Du bist eine KI für konstruktive Kritik.
    Bewerte den Kommentar für X.com, das im Session-State-Key '{STATE_CURRENT_DOC}' bereitgestellt wird und der sowohl kritisch als auch ironisch auf das Thema '{STATE_INITIAL_TOPIC}' eingehen soll.
    Verwende nicht die Wörter: Dividende, Finanzmärkte oder Shareholder.
    Gib 1-2 kurze Verbesserungsvorschläge (z.B. "Gestalte es spannender", "Füge mehr Details hinzu").
    Rufe das Tool 'stop_tool' auf, wenn es keine Kritik gibt.
    Gib ansonsten *nur* die Kritik aus.
    """,
    description="Begutachtet den aktuellen Kommentarentwurf.",
    output_key=STATE_CRITICISM,  # Saves critique to state
    tools=[stop_tool]
)

# Create the LoopAgent
loop_agent = LoopAgent(
    name="LoopAgent", sub_agents=[writer_agent, critic_agent], max_iterations=10
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
        # if event.actions.escalate:
        #     print("escalate")
        if event.is_final_response():
            final_response = event.content.parts[0].text.strip()
            print("Agenten-Antwort: ", final_response, end="\n\n")


asyncio.run(call_agent("execute"))
