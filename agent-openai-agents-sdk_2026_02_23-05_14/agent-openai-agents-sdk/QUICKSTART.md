# Quick Start Guide - Databricks OpenAI Agents SDK

## 🚀 Automated Setup (Recommended)

### Option 1: Using the official quickstart

```bash
cd agent-openai-agents-sdk_2026_02_23-05_14/agent-openai-agents-sdk
uv run quickstart
```

### Option 2: Using the setup script

```bash
cd agent-openai-agents-sdk_2026_02_23-05_14/agent-openai-agents-sdk
chmod +x setup.sh
./setup.sh
```

Both options will:

- ✓ Check prerequisites (uv, nvm, Node.js, Databricks CLI)
- ✓ Authenticate with Databricks
- ✓ Create an MLflow experiment for tracing
- ✓ Configure your `.env` file
- ✓ Install dependencies

## 📋 Manual Setup

If you prefer to set up manually or if automated setup fails:

### 1. Install Prerequisites

**Install uv (Python package manager):**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Install Databricks CLI:**

```bash
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
```

**Install Node.js 20 (via nvm):**

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20
```

### 2. Authenticate with Databricks

#### Option A: OAuth (Recommended)

```bash
databricks auth login
```

#### Option B: Personal Access Token

1. Generate a PAT in Databricks workspace: Settings → Developer → Access Tokens
2. Update `.env` file:

   ```bash
   DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
   DATABRICKS_TOKEN=dapi_your_token_here
   ```

### 3. Create MLflow Experiment

```bash
# Get your username
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)

# Create experiment
databricks experiments create-experiment /Users/$DATABRICKS_USERNAME/agents-on-apps
```

Copy the experiment ID from the output.

### 4. Configure Environment Variables

Update the `.env` file with your experiment ID:

```bash
MLFLOW_EXPERIMENT_ID=your_experiment_id_here
```

### 5. Install Dependencies

```bash
uv sync
```

## ▶️ Running the Agent

### Start the Agent Server + Chat UI

```bash
uv run start-app
```

This starts:

- **Agent Server** at `http://localhost:8000/invocations`
- **Chat UI** at `http://localhost:3000`

### Server Options

**Start with hot-reload (for development):**

```bash
uv run start-server --reload
```

**Change port:**

```bash
uv run start-server --port 8001
```

**Multiple workers:**

```bash
uv run start-server --workers 4
```

## 🧪 Testing the Agent

### Via Chat UI

Open `http://localhost:3000` in your browser

### Via REST API

**Streaming request:**

```bash
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{"role": "user", "content": "What is 2+2?"}],
    "stream": true
  }'
```

**Non-streaming request:**

```bash
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{"role": "user", "content": "What is 2+2?"}]
  }'
```

## 📊 Viewing Traces

Your agent interactions are automatically traced to MLflow.

**View in Databricks:**

1. Go to your Databricks workspace
2. Navigate to: Machine Learning → Experiments
3. Find: `/Users/<your-username>/agents-on-apps`

## 🛠️ Customization

### Adding Tools to Your Agent

Edit `agent_server/agent.py` to add custom tools:

```python
from openai.agents import function_tool

@function_tool
def my_custom_tool(param: str) -> str:
    """Description of what the tool does."""
    return f"Result: {param}"
```

### Adding Dependencies

```bash
uv add package-name
```

## 🚨 Troubleshooting

### "Authentication failed"

- Run `databricks auth login` again
- Check that your workspace URL is correct
- Ensure you have network access to Databricks

### "Cannot find experiment"

- Verify `MLFLOW_EXPERIMENT_ID` in `.env` is set correctly
- Check experiment exists: `databricks experiments list`

### "Module not found"

- Run `uv sync` to install dependencies
- Ensure you're in the correct directory

### "Port already in use"

- Stop any existing servers
- Use a different port: `uv run start-server --port 8001`

## 📚 Next Steps

1. **Customize the agent**: Edit `agent_server/agent.py`
2. **Add tools**: See the Databricks Agent Framework documentation
3. **Deploy to Databricks**: See `DEPLOYMENT.md`
4. **Review architecture**: See `ARCHITECTURE.md`

## 🔗 Resources

- [Databricks Apps Documentation](https://docs.databricks.com/dev-tools/databricks-apps/)
- [OpenAI Agents SDK](https://platform.openai.com/docs/guides/agents-sdk)
- [MLflow Tracing](https://mlflow.org/docs/latest/genai/tracing/)
- [Agent Framework](https://docs.databricks.com/generative-ai/agent-framework/)
