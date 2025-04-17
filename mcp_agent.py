import asyncio

from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService  # Optional
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types

load_dotenv()


async def get_tools_async():
    """Gets tools from the File System MCP Server."""
    # print("Attempting to connect to MCP Filesystem server...")
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command='npx',
            args=["-y",
                  # "@modelcontextprotocol/server-filesystem",
                  "danielsuguimoto/readonly-filesystem-mcp",
                  "."],
        )
        # For remote servers, you would use SseServerParams instead:
        # connection_params=SseServerParams(url="http://remote-server:port/path", headers={...})
    )
    # MCP requires maintaining a connection to the local MCP Server.
    # exit_stack manages the cleanup of this connection.
    return tools, exit_stack


async def get_agent_async():
    """Creates an ADK Agent equipped with tools from the MCP Server."""
    tools, exit_stack = await get_tools_async()
    # print(f"Fetched {len(tools)} tools from MCP server.")
    root_agent = LlmAgent(
        model='gemini-2.0-flash',
        name='filesystem_assistant',
        instruction='Help user interact with the local filesystem using available tools.',
        tools=tools,
    )
    return root_agent, exit_stack


async def async_main():
    session_service = InMemorySessionService()
    # Artifact service might not be needed for this example
    artifacts_service = InMemoryArtifactService()

    session = session_service.create_session(
        state={}, app_name='mcp_filesystem_app', user_id='user_fs'
    )

    query = "Analyze what kind of software project is in the folder '.'"
    # print(f"User Query: '{query}'")
    content = types.Content(role='user', parts=[types.Part(text=query)])

    root_agent, exit_stack = await get_agent_async()

    runner = Runner(
        app_name='mcp_filesystem_app',
        agent=root_agent,
        artifact_service=artifacts_service,  # Optional
        session_service=session_service,
    )

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

    # Crucial Cleanup: Ensure the MCP server process connection is closed.
    await exit_stack.aclose()


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")
