# Command Reference - Databricks Agent

Quick reference for common commands when working with the Databricks OpenAI Agents SDK.

## 🚀 Setup Commands

```bash
# Initial setup (automated)
uv run quickstart

# Verify setup is correct
uv run verify-setup

# Manual authentication
databricks auth login

# Create MLflow experiment manually
databricks experiments create-experiment /Users/<username>/agents-on-apps

# Install/update dependencies
uv sync
uv add <package-name>        # Add a new package
```

## ▶️ Running the Agent

```bash
# Start server + UI (production mode)
uv run start-app

# Start server only (development mode with hot-reload)
uv run start-server --reload

# Start on custom port
uv run start-server --port 8001

# Start with multiple workers
uv run start-server --workers 4
```

## 🧪 Testing Commands

```bash
# Test via curl (non-streaming)
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": [{"role": "user", "content": "Hello!"}]}'

# Test via curl (streaming)
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": [{"role": "user", "content": "Hello!"}], "stream": true}'

# Run agent evaluation
uv run agent-evaluate

# Discover available tools
uv run discover-tools
```

## 🔍 Debugging Commands

```bash
# Check Databricks authentication
databricks current-user me

# List Databricks profiles
databricks auth profiles

# View MLflow experiments
databricks experiments list

# Check environment variables
cat .env

# View server logs (when running)
# Logs appear in terminal where you ran start-app/start-server
```

## 📦 Dependency Management

```bash
# Show installed packages
uv pip list

# Update all dependencies
uv sync --upgrade

# Add a package
uv add requests

# Add a dev dependency
uv add --dev pytest

# Remove a package
uv remove <package-name>

# Export requirements
uv pip freeze > requirements.txt
```

## 🔧 Development Workflow

```bash
# 1. Make changes to agent_server/agent.py

# 2. Test locally with hot-reload
uv run start-server --reload

# 3. Open browser to http://localhost:3000

# 4. Check traces in MLflow experiment

# 5. Run tests (if available)
pytest

# 6. When ready, commit changes
git add .
git commit -m "Updated agent logic"
```

## 🚢 Deployment Commands

```bash
# Deploy to Databricks (requires databricks CLI config)
databricks apps create <app-name>

# Update existing app
databricks apps update <app-name>

# View app status
databricks apps status <app-name>

# View app logs
databricks apps logs <app-name>

# Delete app
databricks apps delete <app-name>
```

## 📊 MLflow Commands

```bash
# List experiments
databricks experiments list

# Get experiment details
databricks experiments get --experiment-id <id>

# Search for runs
databricks runs search --experiment-ids <id>

# View run details
databricks runs get --run-id <run-id>
```

## 🛠️ Troubleshooting

```bash
# Reset authentication
databricks auth logout
databricks auth login

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Reinstall dependencies
rm -rf .venv
uv sync

# Check ports in use
lsof -i :8000        # Agent server
lsof -i :3000        # Chat UI

# Kill process on port
kill -9 $(lsof -t -i:8000)
```

## 📝 Configuration Files

```bash
# Main configuration
.env                          # Environment variables
pyproject.toml                # Python project config
app.yaml                      # Databricks app config

# Agent code
agent_server/agent.py         # Main agent logic
agent_server/start_server.py  # Server initialization
agent_server/utils.py         # Utility functions

# Setup scripts
scripts/quickstart.py         # Automated setup
scripts/start_app.py          # Start server + UI
verify_setup.py               # Verification script
```

## 🌐 URLs (when running locally)

- **Chat UI**: <http://localhost:3000>
- **Agent API**: <http://localhost:8000/invocations>
- **API Docs**: <http://localhost:8000/docs>
- **Health Check**: <http://localhost:8000/health>

## 💡 Pro Tips

```bash
# Use aliases for common commands
echo 'alias agent-start="uv run start-app"' >> ~/.bashrc
echo 'alias agent-dev="uv run start-server --reload"' >> ~/.bashrc
echo 'alias agent-verify="uv run verify-setup"' >> ~/.bashrc

# Source the aliases
source ~/.bashrc

# Now use:
agent-start      # Start the agent
agent-dev        # Start in dev mode
agent-verify     # Verify setup
```

## 📚 Getting Help

```bash
# Command help
uv --help
databricks --help
databricks apps --help

# View documentation
cat README.md
cat QUICKSTART.md
cat ARCHITECTURE.md

# Check version
uv --version
databricks --version
python --version
node --version
```
