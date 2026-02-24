# 🤖 Agent Preview & Overview

## Agent Profile

**Name:** Code Execution Agent
**Framework:** Databricks OpenAI Agents SDK (MLflow ResponsesAgent)
**Model:** `databricks-gpt-5-2`
**Architecture:** FastAPI + WebSocket + MCP Protocol
**Status:** ✅ Ready to Deploy

---

## 🎯 Agent Capabilities

This is a **conversational code execution agent** that can:

- ✅ Execute Python code on Databricks
- ✅ Perform data analysis and transformations
- ✅ Provide real-time streaming responses
- ✅ Handle both synchronous and streaming requests
- ✅ Integrate with Databricks tools via MCP protocol
- ✅ Support multi-turn conversations

---

## 🏗️ Architecture Overview

```text
User Interface (Browser/Web)
        ↓
FastAPI Server (Port 8000)
  ├─ /invocations (streaming & non-streaming)
  ├─ /chat (WebSocket connections)
  └─ MLflow Tracing Integration
        ↓
Agent Runtime (OpenAI Agents Framework)
  ├─ Model: databricks-gpt-5-2
  ├─ Instructions Processing
  └─ Tool Management
        ↓
MCP Server (Model Context Protocol)
  └─ tools: system.ai.python_exec
        ↓
Databricks Workspace Resources
  ├─ Python Execution
  ├─ Data Access
  └─ ML Assets
```

---

## 📋 Core Components

### 1. **Agent Server** (`agent_server/agent.py`)

**What it does:**

- Initializes the AI agent with model and instructions
- Connects to MCP server for tool access
- Handles both streaming and non-streaming requests
- Processes and sanitizes agent output

**Key Functions:**

```python
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse
    # Non-streaming: Returns complete response

async def stream_handler(request: dict) -> AsyncGenerator[ResponsesAgentStreamEvent, None]
    # Streaming: Returns real-time response chunks
```

### 2. **FastAPI Server** (`agent_server/start_server.py`)

**What it does:**

- Starts MLflow-compatible agent server
- Enables chat proxy for UI interactions
- Provides REST API endpoints

**Endpoints:**

- `POST /invocations` - Send agent requests
- `WebSocket /chat` - Real-time chat interface

### 3. **Utilities** (`agent_server/utils.py`)

**What it does:**

- Builds MCP server URLs
- Handles workspace authentication
- Processes stream events
- Sanitizes output for validation

---

## 🚀 How to Preview/Run the Agent

### **Quick Start (Recommended)**

```bash
cd agent-openai-agents-sdk_2026_02_23-05_14/agent-openai-agents-sdk

# One-command setup and start
uv run quickstart
```

This will:

1. ✅ Verify prerequisites (Python, Node.js, CLI)
2. ✅ Authenticate with Databricks
3. ✅ Create MLflow experiment for tracing
4. ✅ Start Agent Server on `http://localhost:8000`
5. ✅ Start Chat UI on `http://localhost:3000`

### **Manual Start (Requires Setup)**

```bash
# Terminal 1: Start Agent Server
uv run start-server

# Terminal 2: Start Chat UI (in agent-openai-agents-sdk directory)
npm install && npm start
```

---

## 💬 How to Interact with the Agent

### **Option 1: Web Chat UI** (Easiest)

```text
1. Open http://localhost:3000
2. Type your message in the chat box
3. Agent executes code and returns results in real-time
4. View conversation history
```

### **Option 2: REST API** (For Testing)

**Streaming Request:**

```bash
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{"role": "user", "content": "Calculate the square root of 16"}],
    "stream": true
  }'
```

**Non-Streaming Request:**

```bash
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{"role": "user", "content": "What is 2 + 2?"}]
  }'
```

### **Option 3: Python Code**

```python
import requests

response = requests.post(
    "http://localhost:8000/invocations",
    json={
        "input": [{"role": "user", "content": "Execute: print('Hello Agent')"}],
        "stream": False
    }
)

print(response.json())
```

---

## 📊 Example Interactions

### **Example 1: Simple Calculation**

```text
User: "What is the sum of 1 + 2 + 3 + 4 + 5?"

Agent:
I'll calculate the sum for you.

(Executes: sum([1, 2, 3, 4, 5]))

Result: 15
```

### **Example 2: Data Analysis**

```text
User: "Create a list of numbers from 1 to 10 and calculate the average"

Agent:
(Executes Python code)
- Creates list: [1, 2, 3, ..., 10]
- Calculates average: mean = 5.5
- Returns result with explanation
```

### **Example 3: Multi-turn Conversation**

```text
User (Turn 1): "Generate a list of random numbers"
Agent: Returns 10 random numbers

User (Turn 2): "Find the maximum value in that list"
Agent: Analysis with result (maintains context from Turn 1)
```

---

## 🔌 Tool Integration

### **Available Tools**

The agent has access to:

1. **Python Executor** (`system.ai.python_exec`)

   - Execute arbitrary Python code
   - Access to standard libraries
   - Data manipulation and analysis
   - ML model inference

2. **Databricks Resources** (via Workspace Client)

   - SQL queries
   - Table access
   - Vector search
   - Job execution

### **Adding More Tools**

Edit `agent_server/agent.py`:

```python
from agents import function_tool

@function_tool
def custom_tool(param: str) -> str:
    """Description of your custom tool."""
    return f"Result: {param}"

# Then add to agent initialization:
agent = Agent(
    name="Code execution agent",
    mcp_servers=[mcp_server],
    tools=[custom_tool]  # Add here
)
```

---

## 📈 Monitoring & Tracing

### **MLflow Integration**

All agent interactions are automatically traced:

1. **View Traces in Databricks:**

   - Go to `Machine Learning → Experiments`
   - Browse: `/Users/<your-username>/agents-on-apps`
   - See latency, token usage, tools called

2. **Trace Details Captured:**

   - ✅ User input messages
   - ✅ Model output
   - ✅ Tool executions
   - ✅ Latency metrics
   - ✅ Error details

### **Local Debugging**

```python
# Enable detailed logs
import logging
logging.basicConfig(level=logging.DEBUG)

# Start server with logging
uv run start-server --log-level DEBUG
```

---

## 🧪 Testing the Agent

### **Test 1: Server Health**

```bash
curl http://localhost:8000/health
```

### **Test 2: Simple Execution**

```bash
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": [{"role": "user", "content": "2+2"}], "stream": false}'
```

### **Test 3: Streaming Test**

```bash
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": [{"role": "user", "content": "print(\"streaming\")"}], "stream": true}'
```

### **Test 4: Multi-turn Conversation**

```bash
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "input": [
      {"role": "user", "content": "Set x = 10"},
      {"role": "assistant", "content": "x is now 10"},
      {"role": "user", "content": "What is x * 5?"}
    ],
    "stream": false
  }'
```

---

## 📁 Project Structure

```text
agent-openai-agents-sdk/
├── agent_server/
│   ├── agent.py              # Agent definition and handlers
│   ├── start_server.py       # FastAPI server startup
│   ├── evaluate_agent.py     # Agent evaluation/scoring
│   └── utils.py              # Helper functions
├── scripts/
│   ├── quickstart.py         # One-command setup
│   ├── start_app.py          # Start server + UI
│   └── discover_tools.py     # Find available tools
├── templates/
│   ├── AGENT_IMPLEMENTATION_TEMPLATE.py
│   ├── AGENT_DOCUMENTATION_TEMPLATE.md
│   └── app.yaml.template
├── pyproject.toml            # Python dependencies
├── requirements.txt          # Quick dependencies
├── databricks.yml            # Databricks bundle config
├── app.yaml                  # Chat UI config
├── .env                      # Environment variables (create this)
└── README.md                 # Full documentation
```

---

## ⚙️ Configuration Files

### **.env** (Required - Create This)

```env
# Databricks Authentication
DATABRICKS_CONFIG_PROFILE=DEFAULT
# or:
# DATABRICKS_HOST=https://your-workspace.databricks.com
# DATABRICKS_TOKEN=dapi_xxxxx

# MLflow Tracing
MLFLOW_EXPERIMENT_ID=your-experiment-id

# Optional
DEBUG=false
LOG_LEVEL=INFO
```

### **databricks.yml** (Bundle Config)

```yaml
bundle:
  name: agent-openai-agents-sdk
  target: dev

resources:
  apps:
    agent_openai_agents_sdk:
      source_path: .
      config:
        command: [python, -m, agent_server.start_server]
```

### **app.yaml** (Chat UI Config)

```yaml
title: Code Execution Agent
description: Conversational agent with code execution
command: npm start
port: 3000
```

---

## 🔐 Security & Best Practices

### **Before Production:**

1. **Environment Variables**

   - ✅ Never commit `.env` files
   - ✅ Use Databricks Secrets for tokens
   - ✅ Rotate PATs regularly

2. **Code Execution Safety**

   - ✅ Agent runs code in Databricks workspace
   - ✅ Databricks enforces resource limits
   - ✅ Enable audit logging
   - ✅ Monitor tool usage

3. **Authentication**

   - ✅ Use OAuth or PAT (not passwords)
   - ✅ Enable MFA on workspace
   - ✅ Restrict API token scope

4. **Deployment**

   - ✅ Use Databricks apps for hosting
   - ✅ Enable HTTPS/TLS
   - ✅ Review permissions in `databricks.yml`

---

## 🐛 Troubleshooting

### **Issue: "Cannot connect to Databricks"**

```bash
# Fix: Authenticate again
databricks auth login

# Verify
databricks current-user me
```

### **Issue: "ModuleNotFoundError" or import errors**

```bash
# Fix: Install dependencies
uv sync
# or
pip install -r requirements.txt
```

### **Issue: "Port 8000/3000 already in use"**

```bash
# Use different port
uv run start-server --port 8001
```

### **Issue: "MLflow experiment not found"**

```bash
# Create new experiment
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks experiments create-experiment /Users/$DATABRICKS_USERNAME/agents-on-apps
```

---

## 📚 Quick Reference Commands

| Task | Command |
| ---- | ------- |
| **Setup (First Time)** | `uv run quickstart` |
| **Start Agent Server** | `uv run start-server` |
| **Start Chat UI** | `npm start` (in agent dir) |
| **Start Both** | `uv run start-app` |
| **Discover Tools** | `uv run discover-tools` |
| **Deploy to Databricks** | `databricks bundle deploy` |
| **View Logs** | `databricks apps logs <app-name> --follow` |
| **Run Tests** | `pytest tests/` |
| **Format Code** | `black agent_server/` |

---

## 🎓 Next Steps

1. **Run the Agent:** `uv run quickstart` or `uv run start-app`
2. **Interact via Chat UI:** Open `http://localhost:3000`
3. **Test the API:** Use the curl examples above
4. **Monitor Traces:** Check MLflow experiment in Databricks
5. **Customize:** Edit `agent_server/agent.py` to add instructions
6. **Deploy:** Use `databricks bundle deploy` when ready

---

## 📖 Additional Resources

- **[QUICKSTART.md](./QUICKSTART.md)** - Detailed setup guide
- **[AGENTS.md](./AGENTS.md)** - Agent development guide
- **[README.md](./README.md)** - Full project documentation
- **[CHECKLIST.md](./CHECKLIST.md)** - Setup verification checklist
- **[COMMANDS.md](./COMMANDS.md)** - All available commands

---

**Ready to preview your agent?** Run: `uv run start-app` 🚀
