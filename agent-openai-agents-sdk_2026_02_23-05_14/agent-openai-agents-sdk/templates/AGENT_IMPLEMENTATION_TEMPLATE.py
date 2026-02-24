"""
Professional Agent Implementation Template
===========================================

This template provides a boilerplate for creating new agents with standard
structure, configuration, and capabilities using the Databricks AI Agents SDK.

Usage:
------
1. Copy this file and modify the agent-specific logic
2. Replace placeholders: [AGENT_NAME], [DESCRIPTION], [MODEL], etc.
3. Implement custom tools and instructions as needed
4. Configure MCP servers and endpoints

Key Components:
- Agent initialization with model and instructions
- MCP server integration for tool access
- Async request/response handlers
- Error handling and validation
- Logging and observability
"""

from typing import AsyncGenerator, Optional, Any
from databricks.sdk import WorkspaceClient
import mlflow
from agents import Agent, Runner
from agents.tracing import set_trace_processors
from databricks_openai import AsyncDatabricksOpenAI
from databricks_openai.agents import McpServer
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)
import logging

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration & Setup
# ============================================================================

# Initialize OpenAI client and tracing
AsyncDatabricksOpenAI()
set_trace_processors([])
mlflow.openai.autolog()


class [AGENT_NAME]Config:
    """Configuration for [AGENT_NAME]."""

    # Core agent settings
    AGENT_NAME = "[AGENT_NAME]"
    AGENT_MODEL = "databricks-gpt-5-2"  # Update to your preferred model
    AGENT_DESCRIPTION = "[Brief description of agent capabilities and purpose]"

    # Instructions for agent behavior
    AGENT_INSTRUCTIONS = """
    You are [AGENT_NAME], a specialized agent designed to [describe purpose].

    Capabilities:
    - [Capability 1]
    - [Capability 2]
    - [Capability 3]

    Instructions:
    1. [Key behavior rule 1]
    2. [Key behavior rule 2]
    3. Always validate user inputs before processing
    4. Provide clear explanations for your actions
    5. Handle errors gracefully and inform users
    """

    # MCP server settings
    MCP_SERVER_URL = "/api/2.0/mcp/functions/system/ai"
    MCP_SERVER_NAME = "system.ai UC function MCP server"

    # Tool settings
    TOOLS = [
        # Add tool definitions here
        # Example: "system.ai.python_exec"
    ]

    # Timeout settings
    REQUEST_TIMEOUT_SECONDS = 300
    MAX_RETRIES = 3


# ============================================================================
# MCP Server Initialization
# ============================================================================

async def initialize_mcp_server(
    workspace_client: Optional[WorkspaceClient] = None,
) -> McpServer:
    """
    Initialize the Model Context Protocol server for tool access.

    Args:
        workspace_client: Databricks workspace client (optional)

    Returns:
        McpServer: Configured MCP server instance

    Raises:
        RuntimeError: If MCP server initialization fails
    """
    try:
        mcp_server = McpServer(
            url=[AGENT_NAME]Config.MCP_SERVER_URL,
            name=[AGENT_NAME]Config.MCP_SERVER_NAME,
            workspace_client=workspace_client,
        )
        logger.info("MCP server initialized successfully")
        return mcp_server
    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {str(e)}")
        raise RuntimeError(f"MCP server initialization failed: {str(e)}")


# ============================================================================
# Agent Factory
# ============================================================================

def create_agent(mcp_server: McpServer) -> Agent:
    """
    Factory function to create and configure the agent.

    Args:
        mcp_server: Initialized MCP server for tool access

    Returns:
        Agent: Configured agent instance ready for use
    """
    agent = Agent(
        name=[AGENT_NAME]Config.AGENT_NAME,
        instructions=[AGENT_NAME]Config.AGENT_INSTRUCTIONS,
        model=[AGENT_NAME]Config.AGENT_MODEL,
        mcp_servers=[mcp_server],
        # Optional: Add custom tools, function definitions, etc.
        # tools=[...],
        # function_definitions=[...],
    )

    logger.info(f"Agent '{[AGENT_NAME]Config.AGENT_NAME}' created successfully")
    return agent


# ============================================================================
# Custom Tool Handlers
# ============================================================================

async def custom_tool_handler(
    tool_name: str,
    tool_input: dict,
    **kwargs,
) -> Any:
    """
    Custom handler for agent tools.

    Override this method to implement custom tool logic beyond MCP.

    Args:
        tool_name: Name of the tool being invoked
        tool_input: Input parameters for the tool
        **kwargs: Additional context

    Returns:
        Tool execution result
    """
    logger.info(f"Executing custom tool: {tool_name}")
    # Implement custom tool logic here
    return {"status": "success", "result": None}


# ============================================================================
# Request/Response Handlers
# ============================================================================

@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    """
    Handle single agent invocation requests.

    This handler processes non-streaming requests and returns complete responses.

    Args:
        request: Agent request containing messages and context

    Returns:
        ResponsesAgentResponse: Agent response with output items

    Raises:
        ValueError: If request validation fails
        RuntimeError: If agent execution fails
    """
    try:
        # Validate request
        if not request or not request.input:
            raise ValueError("Invalid request: empty input")

        # Initialize workspace client
        workspace_client = WorkspaceClient()

        # Initialize MCP server and agent
        async with await initialize_mcp_server(workspace_client) as mcp_server:
            agent = create_agent(mcp_server)

            # Prepare messages
            messages = [item.model_dump() for item in request.input]

            # Execute agent
            logger.info(f"Processing request with {len(messages)} messages")
            result = await Runner.run(agent, messages)

            # Prepare response
            output = sanitize_output_items(result.new_items)
            return ResponsesAgentResponse(output=output)

    except ValueError as e:
        logger.error(f"Request validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Agent invocation failed: {str(e)}")
        raise RuntimeError(f"Agent execution failed: {str(e)}")


@stream()
async def stream_handler(request: dict) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    """
    Handle streaming agent requests.

    This handler supports streaming responses for real-time agent interactions.

    Args:
        request: Agent request containing messages and context

    Yields:
        ResponsesAgentStreamEvent: Individual stream events from agent execution

    Raises:
        ValueError: If request validation fails
        RuntimeError: If agent execution fails
    """
    try:
        # Validate request
        if not request or not request.get("input"):
            raise ValueError("Invalid request: empty input")

        # Initialize workspace client
        workspace_client = WorkspaceClient()

        # Initialize MCP server and agent
        async with await initialize_mcp_server(workspace_client) as mcp_server:
            agent = create_agent(mcp_server)

            # Prepare messages
            messages = [item.model_dump() for item in request.get("input", [])]

            # Execute agent with streaming
            logger.info(f"Processing streaming request with {len(messages)} messages")
            result = Runner.run_streamed(agent, input=messages)

            # Yield stream events
            async for event in process_agent_stream_events(result.stream_events()):
                yield event

    except ValueError as e:
        logger.error(f"Request validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Streaming failed: {str(e)}")
        raise RuntimeError(f"Stream execution failed: {str(e)}")


# ============================================================================
# Utility Functions
# ============================================================================

def sanitize_output_items(items: list) -> list:
    """
    Sanitize agent output items for response.

    Removes sensitive data and ensures safe serialization.

    Args:
        items: Raw output items from agent

    Returns:
        Sanitized output items
    """
    sanitized = []
    for item in items:
        # Remove sensitive fields
        if hasattr(item, "model_dump"):
            sanitized_item = item.model_dump(exclude={"api_key", "secret"})
        else:
            sanitized_item = item
        sanitized.append(sanitized_item)
    return sanitized


async def process_agent_stream_events(
    events: AsyncGenerator,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    """
    Process and transform raw agent stream events.

    Args:
        events: Raw stream events from agent

    Yields:
        Transformed ResponsesAgentStreamEvent instances
    """
    async for event in events:
        # Transform event as needed
        yield event


# ============================================================================
# Health Check & Monitoring
# ============================================================================

async def health_check() -> dict:
    """
    Health check for agent configuration and dependencies.

    Returns:
        dict: Health status with component details
    """
    try:
        workspace_client = WorkspaceClient()
        async with await initialize_mcp_server(workspace_client) as mcp_server:
            return {
                "status": "healthy",
                "agent": [AGENT_NAME]Config.AGENT_NAME,
                "model": [AGENT_NAME]Config.AGENT_MODEL,
                "mcp_server": "connected",
            }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "agent": [AGENT_NAME]Config.AGENT_NAME,
            "error": str(e),
        }


if __name__ == "__main__":
    import asyncio

    # Quick test
    health = asyncio.run(health_check())
    print(f"Agent Health: {health}")
