import asyncio
import json
import mimetypes

from dotenv import load_dotenv
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.models import LlmRequest, LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext, FunctionTool
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()


class FileTaskInput(BaseModel):
    filename: str = Field(description="The name of the file to fetch from the filesystem.")
    user_prompt: str = Field(description="What the user wants to do with this file.")


def set_user_prompt(callback_context: CallbackContext, llm_request: LlmRequest):
    """
    Callback that reads the file and sets the user prompt for the model accordingly.
    """
    args = json.loads(callback_context.user_content.parts[0].text)
    filename = args["filename"]
    try:
        with open(filename, "rb") as f:
            file_content = f.read()
    except FileNotFoundError:
        return LlmResponse(content=types.Content(
            role="model",
            parts=[types.Part(text=f"The file {filename} was not found.")]))
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    file_artifact = types.Part.from_bytes(
        data=file_content,
        mime_type=mime_type,
    )
    user_prompt = types.Part.from_text(text=args["user_prompt"])
    llm_request.contents[0].parts = [user_prompt, file_artifact]


def get_file_agent():
    """
    Creates an ADK Agent that executes a task defined by the user on a file provided by the user.
    """
    return LlmAgent(
        model='gemini-2.5-flash-preview-04-17',
        name='file_agent',
        description="Executes a task defined by the user on a file provided by the user",
        instruction="""
        Execute the task defined by the user on the file that is provided by the user.
        """,
        input_schema=FileTaskInput,
        before_model_callback=set_user_prompt
    )


async def summarize_file_by_name(filename: str, user_prompt: str, tool_context: ToolContext):
    """
    Fetches a file by filename and summarizes its content.

    Args:
        filename (str): The name of the file to fetch from the filesystem
        user_prompt (str): What the user wants to do with this file.

    Returns:
        str: The summarized content
    """
    agent_tool = AgentTool(get_file_agent())
    agent_output = await agent_tool.run_async(
        args={"filename": filename, "user_prompt": user_prompt},
        tool_context=tool_context)
    return agent_output


async def get_root_agent():
    """
    Creates an Agent that works as an assistent.
    """
    return LlmAgent(
        model='gemini-2.5-flash-preview-04-17',
        name='assistant',
        instruction="""
        You are a helpful assistent that answers the user's questions.
        """,
        tools=[FunctionTool(summarize_file_by_name)],
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
            if not event:
                print("EVENT IS INVALID!")
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
        state={}, app_name='assistent_app', user_id='user_id'
    )

    root_agent = await get_root_agent()

    runner = Runner(
        app_name='assistent_app',
        agent=root_agent,
        artifact_service=artifacts_service,  # Optional
        session_service=session_service,
    )

    await run_agent(runner, session)


if __name__ == '__main__':
    asyncio.run(async_main())
