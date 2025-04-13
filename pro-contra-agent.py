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
GEMINI_MODEL = "gemini-2.0-flash"

# --- State Keys ---
STATE_STATEMENT = "SQL databases are better than NoSQL databases."
STATE_PRO = "supporting_arguments"
STATE_CONTRA = "opposing_arguments"

pro_agent = LlmAgent(
    name="ProAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    You are a participant in a discussion.
    Check the session state for key '{STATE_PRO}'.
    If '{STATE_PRO}' does NOT exist or is empty, write a few (1-2 sentence) arguments that are in favour of the statement in state key '{STATE_STATEMENT}'.
    If the session key '{STATE_PRO}' *already exists* and session key '{STATE_CONTRA}', improve and extend '{STATE_PRO}' to contradict the contra arguments in '{STATE_CONTRA}'."
    Output *only* the story or the exact pass-through message.
    """,
    description="Writes the supporting arguments.",
    output_key=STATE_PRO # Saves output to state
)

# Critic Agent (LlmAgent)
critic_agent = LlmAgent(
    name="ContraAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    You are a participant in a discussion.
    You are against the statement in state key '{STATE_STATEMENT}' and against the supporting arguments in state key '{STATE_PRO}'.
    Check the session state for key '{STATE_CONTRA}'.
    If '{STATE_CONTRA}' does NOT exist or is empty, write a few (1-2 sentence) arguments that are against of the statement in state key '{STATE_STATEMENT}' and against the supporting arguments in state key '{STATE_PRO}'.
    If the session key '{STATE_CONTRA}' *already exists*, improve and extend '{STATE_CONTRA}' to contradict the statement and the supporting arguments"
    Output *only* the story or the exact pass-through message.
    """,
    description="Writes the opposing arguments.",
    output_key=STATE_CONTRA # Saves critique to state
)

# Create the LoopAgent
loop_agent = LoopAgent(
    name="LoopAgent", sub_agents=[pro_agent, critic_agent], max_iterations=5
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
            final_response = event.content.parts[0].text.strip()
            print(f"{event.author}: {final_response}", end="\n\n")

print(f"Statement: {STATE_STATEMENT}", end="\n\n")
call_agent("execute")
