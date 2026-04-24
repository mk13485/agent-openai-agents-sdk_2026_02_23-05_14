import os
from typing import AsyncGenerator

from databricks.sdk import WorkspaceClient
from openai import AsyncOpenAI

import mlflow
from agents import Agent, Runner, set_default_openai_api, set_default_openai_client
from agents.tracing import set_trace_processors
from databricks_openai import AsyncDatabricksOpenAI
from databricks_openai.agents import McpServer
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

from agent_server.utils import (
    build_mcp_url,
    get_user_workspace_client,
    process_agent_stream_events,
    sanitize_output_items,
)

BACKEND = os.getenv("AGENT_BACKEND", "").strip().lower()
if BACKEND not in {"databricks", "openai"}:
    BACKEND = "openai" if os.getenv("OPENAI_API_KEY") else "databricks"

USE_DATABRICKS = BACKEND == "databricks"
MODEL = os.getenv(
    "AGENT_MODEL",
    "databricks-gpt-5-2" if USE_DATABRICKS else "gpt-4.1-mini",
)

# Databricks models are served via Chat Completions-compatible APIs.
if USE_DATABRICKS:
    set_default_openai_client(AsyncDatabricksOpenAI())
    set_default_openai_api("chat_completions")
else:
    # Extension-like mode: standard OpenAI key + model.
    # Optional OPENAI_BASE_URL is supported by the OpenAI SDK.
    set_default_openai_client(AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL") or None))
    set_default_openai_api("chat_completions")

set_trace_processors([])  # only use mlflow for trace processing
mlflow.openai.autolog()


async def init_mcp_server(workspace_client: WorkspaceClient | None = None):
    return McpServer(
        url=build_mcp_url("/api/2.0/mcp/functions/system/ai", workspace_client=workspace_client),
        name="system.ai UC function MCP server",
        workspace_client=workspace_client,
    )


def create_coding_agent(mcp_server: McpServer | None = None) -> Agent:
    mcp_servers = [mcp_server] if mcp_server else []
    return Agent(
        name="Code execution agent",
        instructions="You are a code execution agent. You can execute code and return the results.",
        model=MODEL,
        mcp_servers=mcp_servers,
    )


@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    messages = [i.model_dump() for i in request.input]

    if USE_DATABRICKS:
        workspace_client = WorkspaceClient()
        # Optionally use the user's workspace client for on-behalf-of authentication
        # user_workspace_client = get_user_workspace_client()
        async with await init_mcp_server(workspace_client) as mcp_server:
            agent = create_coding_agent(mcp_server)
            result = await Runner.run(agent, messages)
            return ResponsesAgentResponse(output=sanitize_output_items(result.new_items))

    agent = create_coding_agent()
    result = await Runner.run(agent, messages)
    return ResponsesAgentResponse(output=sanitize_output_items(result.new_items))


@stream()
async def stream_handler(request: dict) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    messages = [i.model_dump() for i in request.input]

    if USE_DATABRICKS:
        workspace_client = WorkspaceClient()
        # Optionally use the user's workspace client for on-behalf-of authentication
        # user_workspace_client = get_user_workspace_client()
        async with await init_mcp_server(workspace_client) as mcp_server:
            agent = create_coding_agent(mcp_server)
            result = Runner.run_streamed(agent, input=messages)

            async for event in process_agent_stream_events(result.stream_events()):
                yield event
        return

    agent = create_coding_agent()
    result = Runner.run_streamed(agent, input=messages)
    async for event in process_agent_stream_events(result.stream_events()):
        yield event
