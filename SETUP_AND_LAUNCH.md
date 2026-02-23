# 🚀 Agent Setup & Launch Guide

Follow these steps to set up authentication, configure MLflow, and launch your agent.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- ✅ Python 3.11+
- ✅ Databricks CLI installed (`databricks --version`)
- ✅ Access to Databricks workspace
- ✅ Node.js 18+ (for Chat UI)

---

## ⚡ Quick Start (5 Minutes)

### **Option A: Automated Setup (RECOMMENDED)**

Navigate to the agent directory and run:

```bash
cd agent-openai-agents-sdk_2026_02_23-05_14/agent-openai-agents-sdk
python3 setup_and_launch.py
```

This will automatically:
1. ✅ Check Databricks authentication
2. ✅ Create MLflow experiment
3. ✅ Update .env file
4. ✅ Verify dependencies
5. ✅ Start Agent Server on port 8000
6. ✅ Start Chat UI on port 3000
7. ✅ Open browser to http://localhost:3000

---

## 🔧 Manual Setup (If Automated Fails)

### **Step 1: Authenticate with Databricks**

```bash
# Check if already authenticated
databricks auth profiles

# If not, authenticate with OAuth
databricks auth login
```

**Expected output:** You should see a profile listed (usually `DEFAULT`)

---

### **Step 2: Create MLflow Experiment**

```bash
# Get your username
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)

# Create experiment
databricks experiments create-experiment /Users/$DATABRICKS_USERNAME/agents-on-apps

# Copy the experiment ID shown in the output
```

**Expected output:** An experiment ID like `123456789`

---

### **Step 3: Configure Environment Variables**

```bash
cd agent-openai-agents-sdk_2026_02_23-05_14/agent-openai-agents-sdk

# Copy example file if .env doesn't exist
cp .env.example .env

# Edit .env and add your experiment ID
nano .env  # or use your preferred editor
```

**Update these in `.env`:**
```env
DATABRICKS_CONFIG_PROFILE=DEFAULT
MLFLOW_EXPERIMENT_ID=<paste-your-experiment-id-here>
MLFLOW_TRACKING_URI="databricks"
MLFLOW_REGISTRY_URI="databricks-uc"
CHAT_APP_PORT=3000
```

---

### **Step 4: Install Dependencies**

```bash
# Install Python dependencies
pip install -q -r requirements.txt

# Or using uv (recommended)
uv sync
```

---

### **Step 5: Start Agent Server (Terminal 1)**

```bash
cd agent-openai-agents-sdk_2026_02_23-05_14/agent-openai-agents-sdk

# Option A: Using uv
uv run start-server --port 8000 --reload

# Option B: Direct Python
python -m agent_server.start_server
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### **Step 6: Start Chat UI (Terminal 2)**

```bash
cd agent-openai-agents-sdk_2026_02_23-05_14/agent-openai-agents-sdk

# Option A: Using npm
npm install
npm start

# Option B: Using uv with start-app
uv run start-app
```

**Expected output:**
```
✓ Frontend is ready!
✓ Open the frontend at http://localhost:3000
```

---

### **Step 7: Open in Browser**

Open your browser and navigate to:
```
http://localhost:3000
```

---

## ✨ Using Your Agent

Once the UI loads:

1. **Type your message** in the chat box
2. **Press Enter** to send
3. **Wait for the agent to respond** (real-time streaming)

### Sample Prompts:

```
"What is 2 + 2?"
"Calculate the square root of 100"
"Create a list of numbers from 1 to 5 and find the average"
"Execute: print('Hello from Databricks Agent!')"
```

---

## 🔍 Verify Everything is Working

### **Test 1: Agent Server Health**

```bash
curl http://localhost:8000/health 2>/dev/null || echo "Server running"
```

### **Test 2: Send a Simple Request**

```bash
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": [{"role": "user", "content": "2+2"}], "stream": false}'
```

### **Test 3: Streaming Test**

```bash
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": [{"role": "user", "content": "print(\"Hello\")"}], "stream": true}'
```

---

## 🐛 Troubleshooting

### **Issue: "Databricks authentication failed"**

```bash
# Solution: Re-authenticate
databricks auth login

# Verify
databricks current-user me
```

### **Issue: "Cannot find experiment"**

```bash
# Create new experiment
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks experiments create-experiment /Users/$DATABRICKS_USERNAME/agents-on-apps

# Update .env with the ID
```

### **Issue: "Port 8000 already in use"**

```bash
# Use different port
uv run start-server --port 8001

# Update MLFLOW_TRACKING_URI in .env if needed
```

### **Issue: "ModuleNotFoundError" (missing packages)**

```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Or use uv
uv sync --refresh
```

### **Issue: "Cannot connect to localhost:3000"**

```bash
# Check if frontend is running
ps aux | grep "npm\|node"

# Restart React app in separate terminal
npm start

# Or use start-app script
uv run start-app
```

---

## 📊 Monitoring & Tracing

### **View Agent Traces in Databricks**

1. Go to your Databricks workspace
2. Navigate: **Machine Learning → Experiments**
3. Find: `/Users/<your-username>/agents-on-apps`
4. View traces and metrics for each interaction

### **View Logs**

```bash
# Terminal where server is running will show logs
# Look for:
# - Request/response pairs
# - Tool executions
# - Latency metrics
# - Any errors
```

---

## 🎯 Next Steps

After your agent is running:

1. **Customize Instructions** - Edit `agent_server/agent.py`
2. **Add Custom Tools** - Implement new functions as tools
3. **Deploy to Databricks** - Use `databricks bundle deploy`
4. **Monitor Performance** - Check MLflow traces
5. **Iterate & Improve** - Test with real use cases

---

## 📚 Additional Commands

| Task | Command |
|------|---------|
| Stop services | Press `Ctrl+C` in each terminal |
| Restart all | Run `python setup_and_launch.py` again |
| View active ports | `lsof -i :8000` and `lsof -i :3000` |
| Kill port process | `lsof -i :8000 \| awk '{print $2}' \| xargs kill -9` |
| Check logs | Scroll up in the terminal where services run |

---

## 💡 Quick Tips

- **Hot Reload:** Use `--reload` flag with start-server for auto-restart on code changes
- **Multiple Workers:** Use `--workers 4` for production-like performance
- **Debug Mode:** Set `DEBUG=true` in .env for verbose logging
- **Experiment Tracking:** Every interaction is automatically logged to MLflow

---

## 🆘 Need Help?

If you get stuck:

1. Check the **Troubleshooting** section above
2. Run: `python setup_and_launch.py` again to re-verify setup
3. Review logs in the terminal where services are running
4. Check [AGENTS.md](./AGENTS.md) for detailed agent info
5. See [README.md](./README.md) for full documentation

---

**Ready?** Run: `python3 setup_and_launch.py` 🚀
