---
description: "OpenAI Agents SDK on Databricks: Templates for creating new agents, MCP server setup patterns, async handler patterns, and MLflow integration conventions."
---

# Agent Development Guidelines

This workspace uses the **OpenAI Agents SDK** with Databricks, MLflow, and MCP for conversational AI applications. Follow these patterns when creating new agents and integrating tools.

---

## Agent Creation Template

### Basic Agent Definition

Agents are defined in `agent_server/agent.py` with a consistent structure:

```python
from agents import Agent
from databricks_openai.agents import McpServer

def create_your_agent_name(mcp_server: McpServer) -> Agent:
    return Agent(
        name="Descriptive Agent Name",
        instructions="You are a [role]. You can [capabilities]. Always [constraints].",
        model="databricks-gpt-5-2",  # Always use explicit Databricks model
        mcp_servers=[mcp_server],      # List of MCP servers for tool access
    )
```

### Naming Conventions

- **Agent names**: Use descriptive, user-facing names (e.g., "Code execution agent", "Data analyst assistant")
- **Function names**: Use `create_{agent_type}_agent()` pattern (e.g., `create_data_analyst_agent()`, `create_code_execution_agent()`)
- **Instruction text**: Start with role ("You are a..."), then capabilities, then constraints

### Agent Instructions Best Practices

```python
def create_customer_support_agent(mcp_server: McpServer) -> Agent:
    return Agent(
        name="Customer Support Agent",
        instructions="""You are a helpful customer support agent.

You can:
- Look up customer information and order history
- Process refunds and cancellations
- Escalate complex issues to human support

Always:
- Be polite and professional
- Summarize what the customer said before taking action
- Confirm actions before executing them (refunds, cancellations)
- Never share sensitive customer data outside the support context""",
        model="databricks-gpt-5-2",
        mcp_servers=[mcp_server],
    )
```

---

## MCP Server Setup Pattern

### Initialize MCP Server

Always use this pattern for MCP server initialization:

```python
from databricks.sdk import WorkspaceClient
from databricks_openai.agents import McpServer
from agent_server.utils import build_mcp_url

async def init_mcp_server(workspace_client: WorkspaceClient | None = None):
    return McpServer(
        url=build_mcp_url("/api/2.0/mcp/functions/system/ai", workspace_client=workspace_client),
        name="system.ai UC function MCP server",
        workspace_client=workspace_client,
    )
```

### Custom MCP Servers

For external or custom MCP servers, follow this pattern:

```python
async def init_custom_mcp_server(url: str, workspace_client: WorkspaceClient | None = None):
    """Initialize a custom MCP server for external tools/APIs."""
    return McpServer(
        url=url,
        name="Custom Tool Server",
        workspace_client=workspace_client,
    )
```

### Context Manager Usage

Always use MCP servers within an async context manager:

```python
async with await init_mcp_server(workspace_client) as mcp_server:
    agent = create_your_agent_name(mcp_server)
    # Use agent...
```

---

## Request/Response Handler Patterns

### Invoke Handler (Single-Turn)

For non-streaming requests, use the `@invoke()` decorator:

```python
from mlflow.genai.agent_server import invoke
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse

@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    workspace_client = WorkspaceClient()
    # Optionally use the user's workspace client:
    # user_workspace_client = get_user_workspace_client()
    
    async with await init_mcp_server(workspace_client) as mcp_server:
        agent = create_your_agent_name(mcp_server)
        messages = [i.model_dump() for i in request.input]  # Convert to dicts
        result = await Runner.run(agent, messages)
        
        # Sanitize output for MLflow compatibility
        return ResponsesAgentResponse(output=sanitize_output_items(result.new_items))
```

### Stream Handler (Multi-Turn)

For streaming requests, use the `@stream()` decorator:

```python
from mlflow.genai.agent_server import stream
from mlflow.types.responses import ResponsesAgentStreamEvent
from typing import AsyncGenerator

@stream()
async def stream_handler(request: dict) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    workspace_client = WorkspaceClient()
    
    async with await init_mcp_server(workspace_client) as mcp_server:
        agent = create_your_agent_name(mcp_server)
        messages = [i.model_dump() for i in request.input]
        result = Runner.run_streamed(agent, input=messages)
        
        async for event in process_agent_stream_events(result.stream_events()):
            yield event
```

---

## Configuration & Initialization (start_server.py)

The server setup follows a fixed pattern:

```python
from dotenv import load_dotenv
from mlflow.genai.agent_server import AgentServer, setup_mlflow_git_based_version_tracking

# Load env vars BEFORE importing agent for proper auth
load_dotenv(dotenv_path=".env", override=True)

# Import agent to register handlers with the server (required)
import agent_server.agent  # noqa: E402

agent_server = AgentServer("ResponsesAgent", enable_chat_proxy=True)
app = agent_server.app  # noqa: F841 (module-level for multiple workers)

setup_mlflow_git_based_version_tracking()

def main():
    agent_server.run(app_import_string="agent_server.start_server:app")
```

**Key points:**
- Always load `.env` **before** importing the agent
- Always import the agent module to auto-register handlers
- Use `AgentServer("ResponsesAgent")` for OpenAI API compatibility
- Export `app` as module-level variable for Uvicorn workers

---

## Output Sanitization

MCP tools may return non-string outputs that need sanitization for MLflow's Pydantic models:

```python
from agent_server.utils import sanitize_output_items

# Single-turn: use in invoke_handler
return ResponsesAgentResponse(output=sanitize_output_items(result.new_items))

# Stream: use in stream_handler
async for event in process_agent_stream_events(result.stream_events()):
    yield event
```

The `sanitize_output_items()` function converts list/object outputs to JSON strings.

---

## Error Handling Pattern

When creating new agents or handlers, include error handling:

```python
from databricks.sdk import WorkspaceClient
import logging

@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    try:
        workspace_client = WorkspaceClient()
        async with await init_mcp_server(workspace_client) as mcp_server:
            agent = create_your_agent_name(mcp_server)
            messages = [i.model_dump() for i in request.input]
            result = await Runner.run(agent, messages)
            return ResponsesAgentResponse(output=sanitize_output_items(result.new_items))
    except Exception as e:
        logging.error(f"Agent invocation failed: {e}", exc_info=True)
        # Return error message to user
        return ResponsesAgentResponse(
            output=[{"type": "text", "text": f"Error: {str(e)}"}]
        )
```

---

## Model Selection

Always specify the Databricks model explicitly in agent creation:

```python
Agent(
    model="databricks-gpt-5-2",  # Default: use explicit model
    # Other options:
    # model="databricks-gpt-4o",
    # model="databricks-meta-llama-3-70b-instruct",
    ...
)
```

**Note:** Some models (like GPT-OSS) use a different OpenAI API format. See code comments for model-specific handling.

---

## MLflow Integration

This template uses MLflow for tracing and evaluation:

```python
import mlflow
from agents import set_default_openai_client, set_default_openai_api
from databricks_openai import AsyncDatabricksOpenAI

# Set up OpenAI client and tracing ONCE at module load
set_default_openai_client(AsyncDatabricksOpenAI())
set_default_openai_api("chat_completions")
set_trace_processors([])  # Only use MLflow for tracing
mlflow.openai.autolog()   # Auto-log all OpenAI calls
```

These imports should only appear once in `agent_server/agent.py`, not repeated in each handler.

---

## Adding a New Agent to Existing Server

To add a new agent to the existing server:

1. **Define the agent** in `agent_server/agent.py`:
   ```python
   def create_new_agent(mcp_server: McpServer) -> Agent:
       return Agent(name="...", instructions="...", model="...", mcp_servers=[...])
   ```

2. **Add a new handler** (invoke or stream) that creates and runs the agent

3. **Ensure the handler uses the `@invoke()` or `@stream()` decorator** to register with the server

4. **Test locally** with `uv run start-app`

5. **Update `databricks.yml`** with any new tool permissions required (see AGENTS.md for details)

---

## File Structure

```
agent_server/
├── __init__.py              # Empty init file
├── agent.py                 # Agent definitions + request handlers
├── start_server.py          # FastAPI server + MLflow setup
├── evaluate_agent.py        # Agent evaluation with MLflow scorers
└── utils.py                 # Helper functions (MCP URL building, sanitization)
```

---

## Testing Patterns

Always test agents locally before deployment:

```bash
# Start the server and chat UI
uv run start-app

# Test via API endpoint
curl -X POST http://localhost:8000/api/2.0/agent/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{"role": "user", "content": "your test message"}]
  }'
```

---

## References

- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- [MLflow ResponsesAgent Documentation](https://mlflow.org/docs/latest/genai/flavors/responses-agent-intro/)
- [Databricks Agent Framework](https://docs.databricks.com/aws/en/generative-ai/agent-framework)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
