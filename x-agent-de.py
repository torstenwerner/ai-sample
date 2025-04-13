import asyncio
from typing import AsyncGenerator

from dotenv import load_dotenv
from google.adk.agents import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
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
STATE_CURRENT_DOC = "current_document"
STATE_CRITICISM = "criticism"


def before_writer_callback(callback_context: CallbackContext) -> None:
    state_criticism = callback_context.state.get(STATE_CRITICISM, "")
    if state_criticism == "":
        return
    additional_criticism = input("Manual criticism: ").strip()
    if additional_criticism != "":
        callback_context.state[STATE_CRITICISM] = f"{state_criticism} {additional_criticism}"
    print()


writer_agent = LlmAgent(
    name="WriterAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    Du bist eine KI für kreatives Schreiben von Kommentaren auf X.com.
    Der User gibt eine recht fragwürdige Aussage wieder und liefert dazu relevante Fakten.
    Überprüfe den Sitzungsstatus für '{STATE_CURRENT_DOC}'.
    Wenn '{STATE_CURRENT_DOC}' NICHT existiert oder leer ist, schreibe einen Kommentar für X.com, der sowohl kritisch als auch subtil ironisch und spöttisch auf die fragwürdige Aussage eingeht.
    Wenn '{STATE_CURRENT_DOC}' bereits existiert und '{STATE_CRITICISM}', verfeinere '{STATE_CURRENT_DOC}' gemäß den Kommentaren in '{STATE_CRITICISM}'.
    Der Kommentar muss im Rahmen der relevanten Fakten liegen.
    Gib *nur* die Geschichte oder die genaue Durchgangsnachricht aus.
    """,
    description="Schreibt oder verbessert einen Kommentarentwurf.",
    before_agent_callback=before_writer_callback,
    output_key=STATE_CURRENT_DOC  # Saves output to state
)

# Critic Agent (LlmAgent)
critic_agent = LlmAgent(
    name="CriticAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    Du bist eine KI für konstruktive Kritik.
    Bewerte den Kommentar für X.com, das im Session-State-Key '{STATE_CURRENT_DOC}' bereitgestellt wird.
    Der Kommentar soll sich auf eine vom User gelieferte fragwürdige Aussage beziehen und im Rahmen der vom User gelieferten relevanten Fakten liegen.
    Gib 1-2 kurze Verbesserungsvorschläge (z.B. "Gestalte es spannender", "Füge mehr Details hinzu").
    Gib *nur* die Kritik aus oder *nur* das Wort 'STOP', wenn es keine Kritik gibt.
    """,
    description="Begutachtet den aktuellen Kommentarentwurf.",
    output_key=STATE_CRITICISM  # Saves critique to state
)


class CheckCondition(BaseAgent):  # Custom agent to check state
    def __init__(self):
        super().__init__(name="CheckCondition")

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get(STATE_CRITICISM, "pending").strip()
        is_done = (status == "STOP")
        yield Event(author=self.name, actions=EventActions(escalate=is_done))  # Escalate if done


# Create the LoopAgent
root_agent = LoopAgent(
    name="LoopAgent", sub_agents=[writer_agent, critic_agent, CheckCondition()], max_iterations=10
)

# Session and Runner
if __name__ == "__main__":
    session_service = InMemorySessionService()
    session = session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)


# Agent Interaction
async def call_agent(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.content is not None and event.is_final_response():
            final_response = event.content.parts[0].text.strip()
            print(f"{event.author}: {final_response}", end="\n\n")


async def main():
    initial_user_prompt = """
    # Fragwürdige Aussage:
    Wir die CDU machen Deutschland wieder leistungsgerecht! Deutschland bekommt wieder eine Politik für die hart arbeitende Mitte – eine Agenda für die Fleißigen. Wer mehr leistet, muss sich mehr leisten können. Wir entlasten Euch und die Unternehmen in unserem Land. Damit sich Leistung wieder lohnt. Der Politikwechsel kommt.
    # Relevante Fakten:
    Die CDU hat die Wähler belogen und macht nun die Politik von SPT und Grünen. Alle Nettosteuerzahler und Unternehmen werden immer stärker belastet. Die CDU hat vor der Wahl einen Politikwechsel versprochen und macht jetzt genau die gleiche Politik wie die Vorgängerregierung. Sie wird die CO2-Steuer weiterführen, was zu extrem hohen Energiepreisen führt.
    """
    print(initial_user_prompt.strip(), end="\n\n")
    await call_agent(initial_user_prompt)


if __name__ == "__main__":
    asyncio.run(main())
