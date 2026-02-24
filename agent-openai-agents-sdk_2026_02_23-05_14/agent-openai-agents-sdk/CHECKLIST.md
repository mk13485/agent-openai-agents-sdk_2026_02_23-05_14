# Getting Started Checklist ✅

Follow this checklist to get your Databricks OpenAI Agents SDK up and running.

## Prerequisites Setup

- [ ] **Install uv** (Python package manager)

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- [ ] **Install Databricks CLI**

  ```bash
  curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
  ```

- [ ] **Install Node.js 20** (for chat UI)

  ```bash
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
  nvm install 20
  nvm use 20
  ```

## Quick Start (Choose One Method)

### Method 1: Automated Setup (Easiest) ⭐

- [ ] **Navigate to agent directory**

  ```bash
  cd agent-openai-agents-sdk_2026_02_23-05_14/agent-openai-agents-sdk
  ```

- [ ] **Run quickstart**

  ```bash
  uv run quickstart
  ```

  This will:
  - Authenticate with Databricks
  - Create MLflow experiment
  - Configure .env file
  - Install dependencies

### Method 2: Alternative Setup Script

- [ ] **Run setup script**

  ```bash
  chmod +x setup.sh
  ./setup.sh
  ```

### Method 3: Manual Setup

- [ ] **Authenticate with Databricks**

  ```bash
  databricks auth login
  ```

- [ ] **Get your username**

  ```bash
  databricks current-user me
  ```

- [ ] **Create MLflow experiment**

  ```bash
  databricks experiments create-experiment /Users/<your-username>/agents-on-apps
  ```

  Note the experiment ID from the output.

- [ ] **Configure .env file**
  - Open `.env` file
  - Add your experiment ID: `MLFLOW_EXPERIMENT_ID=<your-id>`
  - Verify authentication settings

- [ ] **Install dependencies**

  ```bash
  uv sync
  ```

## Verification

- [ ] **Verify setup is correct**

  ```bash
  uv run verify-setup
  ```

  All checks should pass ✓

## Run the Agent

- [ ] **Start the agent and chat UI**

  ```bash
  uv run start-app
  ```

- [ ] **Open chat UI in browser**
  - Navigate to: <http://localhost:3000>

- [ ] **Test the agent**
  - Type a message in the chat
  - Try: "What is 2 + 2?" or "Help me write a Python function"

## Verify It's Working

- [ ] **Check API endpoint**

  ```bash
  curl -X POST http://localhost:8000/invocations \
    -H "Content-Type: application/json" \
    -d '{"input": [{"role": "user", "content": "Hello!"}]}'
  ```

- [ ] **View traces in MLflow**
  - Go to Databricks workspace
  - Navigate to: Machine Learning → Experiments
  - Find: `/Users/<your-username>/agents-on-apps`
  - Verify you see traces from your test interactions

## Customization (Optional)

- [ ] **Read the agent code**
  - Open `agent_server/agent.py`
  - Understand the current implementation

- [ ] **Add custom tools** (if needed)
  - Edit `agent_server/agent.py`
  - Add your custom function tools
  - Restart server to test

- [ ] **Review documentation**
  - [ ] Read `README.md` for overview
  - [ ] Read `QUICKSTART.md` for detailed instructions
  - [ ] Read `COMMANDS.md` for command reference
  - [ ] Read `ARCHITECTURE.md` for system design

## Development Workflow

- [ ] **Set up development mode**

  ```bash
  uv run start-server --reload
  ```

  Now changes auto-reload when you save files

- [ ] **Create a feature branch**

  ```bash
  git checkout -b feature/my-new-feature
  ```

- [ ] **Make your changes**
  - Edit agent code
  - Test in chat UI
  - Review traces in MLflow

- [ ] **Commit your work**

  ```bash
  git add .
  git commit -m "Add feature: my new feature"
  ```

## Next Steps

- [ ] **Explore available tools**

  ```bash
  uv run discover-tools
  ```

- [ ] **Read OpenAI Agents SDK docs**
  - <https://platform.openai.com/docs/guides/agents-sdk>

- [ ] **Read Databricks Agent Framework docs**
  - <https://docs.databricks.com/generative-ai/agent-framework/>

- [ ] **Plan your custom agent features**
  - What tools does your agent need?
  - What data sources will it access?
  - What business logic should it implement?

## Deployment (When Ready)

- [ ] **Review deployment guide**
  - Read `DEPLOYMENT.md`

- [ ] **Deploy to Databricks**

  ```bash
  databricks apps create my-agent-app
  ```

- [ ] **Test production deployment**
  - Verify agent works in Databricks
  - Check logs and traces

- [ ] **Share with team**
  - Configure access permissions
  - Document usage for end users

## Troubleshooting

If you encounter issues:

1. **Run verification**

   ```bash
   uv run verify-setup
   ```

2. **Check authentication**

   ```bash
   databricks current-user me
   ```

3. **Review logs**
   - Check terminal output where agent is running
   - Review MLflow experiment traces

4. **Consult documentation**
   - See `QUICKSTART.md` troubleshooting section
   - See `COMMANDS.md` for debugging commands

5. **Get help**
   - Check Databricks Agent Framework docs
   - Review OpenAI Agents SDK documentation
   - Contact your Databricks support team

## 🎉 Success

Once all items are checked, you have:

- ✅ A working Databricks OpenAI agent
- ✅ Local development environment
- ✅ Tracing and monitoring set up
- ✅ Ready to customize and deploy

**Happy building!** 🚀
