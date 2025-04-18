import asyncio

from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService  # Optional
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types

load_dotenv()


async def get_filesystem_tools_async():
    """Gets tools from the File System MCP Server."""
    return await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command='npx',
            args=["-y",
                  # "@modelcontextprotocol/server-filesystem",
                  "danielsuguimoto/readonly-filesystem-mcp",
                  "."],
        )
    )


async def get_jetbrains_tools_async():
    """Gets tools from the Jetbrains MCP Server."""
    return await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command='npx',
            args=["-y",
                  "@jetbrains/mcp-proxy"],
        )
    )


async def get_agent_async():
    """Creates an ADK Agent equipped with tools from the MCP Server."""
    tools_filesystem, exit_stack_filesystem = await get_filesystem_tools_async()
    tools_jetbrains, exit_stack_jetbrains = await get_jetbrains_tools_async()
    root_agent = LlmAgent(
        # model='gemini-2.0-flash',
        model='gemini-2.5-flash-preview-04-17',
        name='filesystem_assistant',
        instruction='Help user interact with the local filesystem and the Jetbrains IDE using available tools.',
        # tools=tools_filesystem + tools_jetbrains,
        # tools=tools_jetbrains,
        tools=tools_filesystem,
    )
    return root_agent, exit_stack_filesystem, exit_stack_jetbrains


async def run_agent(runner, session):
    # query = "Analyze what kind of software project is in the first folder that you can access."
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
                    elif part.function_response and part.function_response.response['result']:
                        print(f"function_response: isError={part.function_response.response['result'].isError}")
                    else:
                        print(part)


async def async_main():
    session_service = InMemorySessionService()
    # Artifact service might not be needed for this example
    artifacts_service = InMemoryArtifactService()

    session = session_service.create_session(
        state={}, app_name='mcp_filesystem_app', user_id='user_fs'
    )

    root_agent, exit_stack_filesystem, exit_stack_jetbrains = await get_agent_async()

    runner = Runner(
        app_name='mcp_filesystem_app',
        agent=root_agent,
        artifact_service=artifacts_service,  # Optional
        session_service=session_service,
    )

    await run_agent(runner, session)

    # Crucial Cleanup: Ensure the MCP server process connection is closed.
    await exit_stack_filesystem.aclose()
    await exit_stack_jetbrains.aclose()


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")
