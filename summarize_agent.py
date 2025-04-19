import asyncio
import mimetypes

from dotenv import load_dotenv
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types

load_dotenv()


def fetch_file_by_name(filename: str, tool_context: ToolContext):
    """
    Fetches a file by filename and adds it as an artifact with the name 'input_file'.

    Args:
        filename (str): The name of the file to fetch from the filesystem
    """
    with open(filename, "rb") as f:
        file_content = f.read()
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    file_artifact = types.Part.from_bytes(
        data=file_content,
        mime_type=mime_type,
    )
    tool_context.save_artifact("input_file", file_artifact)


def set_user_prompt(callback_context: CallbackContext):
    """
    Callback that sets the artifact with the name 'input_file' as the user prompt for the summarizer agent.
    """
    file_artifact = callback_context.load_artifact("input_file")
    callback_context.user_content.parts = [file_artifact]


def get_summarizer_agent():
    """
    Creates an ADK Agent that summarizes a file in the user prompt.
    The file is set as the user prompt by a callback.
    """
    return LlmAgent(
        model='gemini-2.5-flash-preview-04-17',
        name='summarizer',
        instruction="""
        You are summarizing the content of a single file that is provided by the user.
        """,
        before_agent_callback=set_user_prompt
    )


def get_root_agent():
    """
    Creates an ADK Agent that fetches a file and summarizes it..
    """
    return LlmAgent(
        model='gemini-2.5-flash-preview-04-17',
        name='filesystem_assistant',
        instruction="""
        You are summarizing the content of a single file that is specified by the user.
        1. Fetch the file by its filename using the tool fetch_file_by_name.
        2. Transfer control to the summarizer agent.
        
        Fetch the file again if the user specifies a new filename.
        """,
        tools=[FunctionTool(fetch_file_by_name)],
        sub_agents=[get_summarizer_agent()]
    )


async def run_agent(runner, session):
    while True:
        query = input("You: ")
        if not query.strip():
            print("Exiting interactive session.")
            break

        content = types.Content(role='user', parts=[types.Part(text=query)])

        events_async = runner.run_async(
            session_id=session.id, user_id=session.user_id, new_message=content
        )

        async for event in events_async:
            if event.is_final_response():
                final_response = event.content.parts[0].text.strip()
                print(f"final_response: {final_response}")
            else:
                for part in event.content.parts:
                    if part.text:
                        print(f"text: {part.text.strip()}")
                    elif part.function_call:
                        print(f"function_call: name={part.function_call.name} args={part.function_call.args}")
                    elif part.function_response:
                        print(f"function_response: name={part.function_response.name}")
                    else:
                        print(part)


async def async_main():
    session_service = InMemorySessionService()
    # Artifact service might not be needed for this example
    artifacts_service = InMemoryArtifactService()

    session = session_service.create_session(
        state={}, app_name='mcp_filesystem_app', user_id='user_fs'
    )

    root_agent = get_root_agent()

    runner = Runner(
        app_name='mcp_filesystem_app',
        agent=root_agent,
        artifact_service=artifacts_service,  # Optional
        session_service=session_service,
    )

    await run_agent(runner, session)


if __name__ == '__main__':
    asyncio.run(async_main())
