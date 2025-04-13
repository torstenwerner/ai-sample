from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
APP_NAME = "doc_writing_app"
USER_ID = "dev_user_01"
SESSION_ID = "session_01"
# GEMINI_MODEL = "gemini-2.0-flash-exp" # small rate limit
GEMINI_MODEL = "gemini-2.0-flash"

# --- State Keys ---
STATE_INITIAL_TOPIC = "Dieser neue Koalitionsvertrag ist für viele Wähler sehr unbefriedigend."
STATE_CURRENT_DOC = "current_document"
STATE_CRITICISM = "criticism"

writer_agent = LlmAgent(
    name="WriterAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    Du bist eine KI für kreatives Schreiben.
    Überprüfe den Sitzungsstatus für '{STATE_CURRENT_DOC}'.
    Wenn '{STATE_CURRENT_DOC}' NICHT existiert oder leer ist, schreibe eine sehr kurze (1-2 Sätze) Geschichte oder ein Dokument basierend auf dem Thema im Zustandsschlüssel '{STATE_INITIAL_TOPIC}'.
    Wenn '{STATE_CURRENT_DOC}' bereits existiert und '{STATE_CRITICISM}', verfeinere '{STATE_CURRENT_DOC}' gemäß den Kommentaren in '{STATE_CRITICISM}'.
    Gib *nur* die Geschichte oder die genaue Durchgangsnachricht aus.
    """,
    description="Schreibt den ersten Dokumententwurf.",
    output_key=STATE_CURRENT_DOC # Saves output to state
)

# Critic Agent (LlmAgent)
critic_agent = LlmAgent(
    name="CriticAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    Du bist eine KI für konstruktive Kritik.
    Bewerte das Dokument, das im Session-State-Key '{STATE_CURRENT_DOC}' bereitgestellt wird.
    Gib 1-2 kurze Verbesserungsvorschläge (z.B. "Gestalte es spannender", "Füge mehr Details hinzu").
    Gib *nur* die Kritik aus.
    """,
    description="Reviews the current document draft.",
    output_key=STATE_CRITICISM # Saves critique to state
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
def call_agent(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agenten-Antwort: ", final_response)

call_agent("execute")
