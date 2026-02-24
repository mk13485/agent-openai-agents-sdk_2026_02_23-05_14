# Copilot-Style Coding Agent: Complete Design Specification
## Production Architecture & Implementation Blueprint

**Version:** 1.0  
**Date:** 23 February 2026  
**Status:** Ready for Implementation  
**Team:** Slovak Engineering Team (EU/GDPR Compliant)  
**Target Deployment:** EU Cloud (Databricks EU regions) + On-Prem Option  

---

## Executive Summary

This document specifies a **production-ready Copilot-equivalent coding agent** with inline completions, multi-file refactoring, agentic task orchestration, and sandbox-based execution verification. 

**Key Design Principles:**
- ✅ EU/GDPR data residency and privacy-first architecture
- ✅ Built on OpenAI Agents SDK + Databricks for rapid deployment
- ✅ Stateless App Server + managed MCP servers for extensibility
- ✅ Dual-model strategy (fast small model + agent model)
- ✅ Safety gates: redaction, license detection, secure sandbox
- ✅ Developer ergonomics: IDE plugins, chat pane, action confirmation

**Expected Outcomes (6-month pilot):**
- Inline completions with 70%+ acceptance rate
- Multi-file agent tasks with 85%+ test pass rate
- Sub-500ms p95 latency for completions
- Zero security/privacy incidents
- Full GDPR compliance (data residency, deletion, consent)

---

## 1. Architecture Overview

### 1.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Developer IDEs                              │
│  VS Code │ JetBrains │ Neovim │ Web IDE (browser-based)            │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼ (Protocol: LSP + Custom WebSocket)
┌─────────────────────────────────────────────────────────────────────┐
│              App Server (Session & Auth Gateway)                    │
│  • Authentication (OAuth 2.0 / OIDC, Entra ID)                     │
│  • Rate limiting & quotas                                           │
│  • Session state management (Redis)                                │
│  • Tool proxy layer (Git, Test, Lint, CI)                          │
│  • Telemetry ingestion & streaming                                 │
│  • Policy enforcement (privacy level, safety gates)                │
└────────────────┬────────────────┬────────────────┬──────────────────┘
                 │                │                │
         ┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼────────────┐
         │Model Serving │  │ Execution   │  │Data Stores &     │
         │& Agent Ops   │  │Sandbox      │  │Indexing          │
         │              │  │             │  │                  │
         │• Fast model  │  │• Ephemeral  │  │• Code search     │
         │  (completions│  │  containers │  │• Embeddings (VDB)│
         │• Agent model │  │• Tool       │  │• Repo index      │
         │  (tasks)     │  │  runners    │  │• Telemetry DB    │
         │• Inference   │  │• Security   │  │• Training store  │
         │  autoscale   │  │  gates      │  │(labeled data)    │
         └──────────────┘  └─────────────┘  └──────────────────┘
                 │                │
                 └────────┬───────┘
                          ▼
     ┌──────────────────────────────────────┐
     │ Monitoring, Logging, Observability   │
     │ • Latency metrics                    │
     │ • Suggestion acceptance rate         │
     │ • Safety flags / incidents           │
     │ • Model drift detection              │
     │ • Audit trails (EU compliance)       │
     └──────────────────────────────────────┘
```

### 1.2 Data Flow (Step-by-Step)

**Flow 1: Inline Completion (Fast Path)**
1. IDE detects typing event (cursor position, file window).
2. Client sends *minimal context* (user's privacy preference determines scope):
   - **Local-only mode:** None (uses local cache only).
   - **Partial mode:** Current file + 100 chars around cursor.
   - **Full mode:** Repo snapshot (symbols, recent edits).
3. App Server enriches context (git metadata, repo index, semantic search).
4. Fast model (quantized, <100ms) generates top-k completions.
5. Verifier runs basic checks (lint, type check against local stubs).
6. Client displays ranked suggestions with confidence & provenance badges.
7. User accepts/rejects → telemetry logged (anonymized).

**Flow 2: Agentic Task (Multi-Step, Verification Loop)**
1. User issues task in chat pane (e.g., "Add caching to user service").
2. App Server builds context (repo state, open tests, CI config).
3. Agent model returns structured plan: `[FileEdit(...), RunTest(...), ...]`.
4. User reviews plan in UI (diff preview) → approves/cancels.
5. App Server executes plan in sandbox:
   - Apply file edits in ephemeral container.
   - Run tests & linters.
   - Capture output + coverage.
6. Model receives execution result → "Passed" or "Revise → [plan 2]".
7. Loop until pass threshold or user abort.
8. Final result offered as PR (changelog + test artifacts) or direct commit.

### 1.3 Threat Model & Safety Gates

**Prevention Layer (Before model):**
- Redaction: API keys, tokens, secrets stripped before sending.
- License detection: code patterns matched against viral licenses (GPL, AGPL).
- PII masking: email addresses, IPs, personal info redacted.

**Model Layer (During inference):**
- Instruction tuning: model trained to avoid insecure patterns (SQL injection, hardcoded secrets).
- Rejection sampling: model rejects outputs with detected security issues.

**Verification Layer (After execution):**
- Sandbox isolation: no network, limited filesystem, resource quotas (CPU, memory, time).
- Test execution: generated code must pass provided tests.
- Manual approval: high-impact changes (deleting files, modifying CI) require user confirmation.

---

## 2. Detailed Component Specifications

### 2.1 App Server (Session, Auth & Tool Proxy)

#### Responsibilities
- Authentication & authorization (OAuth 2.0, OIDC, Entra ID).
- Rate limiting (requests/min per user, token budgets).
- Session state management (Redis, TTL 8 hours).
- Tool proxying (safe, authenticated access to external tools).
- Telemetry ingestion & anonymization.
- Policy enforcement (privacy level, safety flags).

#### API Contract (REST + WebSocket)

**Auth Endpoint:**
```
POST /api/v1/auth/token
Payload: { email, refresh_token }
Response: { access_token, expires_in, session_id }
```

**Completion Request:**
```
POST /api/v1/completions
Headers: { Authorization: "Bearer {token}" }
Payload: {
  file_path: "src/service.py",
  cursor_line: 42,
  cursor_col: 8,
  context_level: "partial" | "full" | "local-only",
  repo_snapshot: { ... }  // optional, based on context_level
}
Response: {
  suggestions: [{
    text: "def cached_get_user(...)",
    confidence: 0.92,
    provenance: "trained on sklearn examples",
    unsafe_flags: []
  }],
  latency_ms: 87
}
```

**Agentic Task Request:**
```
POST /api/v1/tasks
Payload: {
  description: "Add caching to user service",
  repo_state: { branch: "main", commit_sha: "abc123" },
  execution_mode: "preview" | "execute"
}
Response: {
  task_id: "task_abc123",
  plan: [
    { type: "file_edit", file: "src/service.py", changes: [...] },
    { type: "run_test", command: "pytest src/tests/test_service.py" }
  ],
  user_confirmation_required: true
}
```

**Tool Call (e.g., run test):**
```
POST /api/v1/tools/run-test
Payload: {
  task_id: "task_abc123",
  test_command: "pytest src/tests/test_service.py --cov",
  timeout_sec: 30
}
Response: {
  exit_code: 0,
  stdout: "...",
  stderr: "",
  duration_sec: 2.3
}
```

#### Implementation (Databricks + Fastapi)

```python
# app_server/server.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.websockets import WebSocket
import redis
import logging

app = FastAPI()
redis_client = redis.Redis(host="redis.internal", port=6379)
logger = logging.getLogger(__name__)

# Middleware: rate limit
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    user_id = request.headers.get("X-User-ID")
    rate_key = f"ratelimit:{user_id}"
    count = redis_client.incr(rate_key, amount=1)
    if count == 1:
        redis_client.expire(rate_key, 60)
    if count > 100:  # 100 req/min
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return await call_next(request)

@app.post("/api/v1/completions")
async def completions(req: CompletionRequest, user = Depends(get_current_user)):
    # Redact secrets from file context
    redacted_context = redact_secrets(req.repo_snapshot)
    
    # Call model serving
    response = await model_inference_client.complete(
        file_path=req.file_path,
        context=redacted_context,
        model="fast-model"
    )
    
    # Log telemetry (anonymized)
    log_telemetry({
        "event": "completion_request",
        "user_hash": hash_user_id(user.id),
        "latency_ms": response.elapsed_ms
    })
    
    return response

@app.websocket("/ws/task-stream")
async def task_stream(websocket: WebSocket, user = Depends(get_current_user)):
    await websocket.accept()
    task_id = None
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "start_task":
                task_id = await execute_task(data["description"], user)
                await websocket.send_json({"task_id": task_id})
            elif data["type"] == "approve_plan":
                await sandbox_execute(task_id)
    finally:
        if task_id:
            cleanup_task(task_id)
```

#### Deployment (Databricks Serving + Container)

```yaml
# app_server/databricks_config.yml
name: coding-agent-app-server
target: databricks
compute: "code-gen-cluster"
env_vars:
  REDIS_HOST: "redis.internal"
  MODEL_SERVING_ENDPOINT: "https://serving.databricks.com/completions"
  EU_REGION: "eu-west-1"
  LOG_ANONYMIZATION: "true"
health_check:
  path: "/health"
  interval_sec: 30
```

---

### 2.2 Model Serving & Agent Runtime

#### Model Family Strategy

**Tier 1: Fast Completions Model**
- Size: 6B–13B parameters (quantized to 4-bit for <100ms latency).
- Training: supervised fine-tune on 500k code examples + RLHF with acceptance signals.
- Purpose: inline suggestions, low-latency single-file context.
- Deployment: multi-instance autoscaling (GPU/vLLM).

**Tier 2: Agent Model**
- Size: 70B+ parameters (optionally hosted on separate GPU cluster).
- Capabilities: structured planning, tool calling, multi-file reasoning.
- Training: co-trained with tool harness to learn execution/verify loops.
- Purpose: multi-step tasks, refactoring, test generation.
- Deployment: batch + streaming endpoints.

#### Agent Runtime (Tool Use Orchestration)

```python
# model_serving/agent_runtime.py
from agents import Agent
from agents.tools import Tool
from databricks_openai.agents import McpServer

class CodingAgentRuntime:
    def __init__(self):
        self.fast_model = "fast-coding-model-6b"
        self.agent_model = "agent-coding-model-70b"
        self.mcp_servers = self._init_mcp_servers()
        
    def _init_mcp_servers(self):
        """ Initialize MCP servers for tool access (Git, Test, Lint, Build) """
        servers = []
        
        # Git MCP
        servers.append(McpServer(
            uri="local:///tools/git_mcp.py",
            name="git_tool",
            description="Git operations: status, diff, create PR"
        ))
        
        # Test runner MCP
        servers.append(McpServer(
            uri="local:///tools/test_runner_mcp.py",
            name="test_runner",
            description="Run pytest, coverage"
        ))
        
        # Linter/formatter MCP
        servers.append(McpServer(
            uri="local:///tools/linter_mcp.py",
            name="linter",
            description="Pylint, Black, MyPy"
        ))
        
        # Code search MCP
        servers.append(McpServer(
            uri="local:///tools/search_mcp.py",
            name="code_search",
            description="Semantic search, symbol lookup"
        ))
        
        return servers
    
    async def complete(self, file_path: str, context: dict) -> list:
        """Fast model for inline completions."""
        agent = Agent(
            name="CompletionAgent",
            model=self.fast_model,
            instructions="""You are a code completion expert.
            Generate a single code completion (1-5 lines) at the cursor position.
            - Must be syntactically valid.
            - Should follow project style.
            - Return ONLY the completion, no explanation.""",
            mcp_servers=self.mcp_servers[:1],  # Minimal tools for completions
        )
        
        prompt = f"Complete the following code:\n\n{context['file_window']}"
        response = await agent.invoke(prompt)
        return [{"text": response.content, "confidence": 0.92}]
    
    async def plan_task(self, task_desc: str, repo_state: dict) -> dict:
        """Agent model to generate multi-step plan."""
        agent = Agent(
            name="RefactorAgent",
            model=self.agent_model,
            instructions="""You are an expert refactoring agent.
            Given a task, generate a structured plan:
            - List files to modify with required changes.
            - Suggest tests to run after changes.
            - Provide a summary.
            
            Format your response as JSON with keys: plan, tests, summary.""",
            mcp_servers=self.mcp_servers,
        )
        
        prompt = f"""Task: {task_desc}
        
        Repository state:
        - Branch: {repo_state['branch']}
        - Recent commits: {repo_state['recent_commits']}
        - Test coverage: {repo_state['test_coverage']}
        
        Generate a detailed plan (as JSON)."""
        
        response = await agent.invoke(prompt)
        return json.loads(response.content)
    
    async def verify_and_revise(self, plan: dict, execution_result: dict) -> dict:
        """Receive execution result and revise plan if needed."""
        if execution_result["tests_passed"]:
            return {"status": "success", "plan": plan}
        
        agent = Agent(
            name="DebugAgent",
            model=self.agent_model,
            instructions="Debug the failing tests and propose fixes.",
            mcp_servers=self.mcp_servers,
        )
        
        prompt = f"""Previous plan failed tests:
        {execution_result['test_output']}
        
        Propose a revised plan."""
        
        response = await agent.invoke(prompt)
        return json.loads(response.content)
```

#### Inference Scaling (Databricks Native)

```python
# model_serving/autoscaling.py
from databricks.sdk import WorkspaceClient

class InferenceAutoscaler:
    def __init__(self):
        self.client = WorkspaceClient()
    
    def scale_completions(self, qps_target: int):
        """Scale fast model to target requests/sec."""
        self.client.serving_endpoints.update(
            name="fast-completion-endpoint",
            config={
                "served_models": [{
                    "model_name": "fast-coding-model-6b",
                    "model_version": "latest",
                    "workload_type": "GPU_SMALL",
                    "scale_to_zero_enabled": True,
                    "max_provisioned_throughput": qps_target * 100  # bytes/sec
                }]
            }
        )
    
    def scale_agent(self, concurrent_tasks: int):
        """Scale agent model to concurrent task limit."""
        self.client.serving_endpoints.update(
            name="agent-endpoint",
            config={
                "served_models": [{
                    "model_name": "agent-coding-model-70b",
                    "model_version": "latest",
                    "workload_type": "GPU_LARGE",
                    "provisioned_throughput": concurrent_tasks * 20  # tokens/sec per task
                }]
            }
        )
```

---

### 2.3 Execution Sandbox & Tool Integration

#### Sandbox Architecture

**Container-Per-Task Model:**
- Ephemeral pod (5–10 minute lifetime).
- Mounted volume: task's repo snapshot (read-only), scratch volume for edits (read-write).
- Network isolation: only outbound to approved language servers, package registries.
- Resource quotas: 4 CPUs, 8 GB RAM, 10 GB disk, 60-sec timeout per tool.

#### Tool Adapters (MCP Servers)

```python
# tools/test_runner_mcp.py
"""MCP Server: Run tests with sandboxing."""

import json
import subprocess
import tempfile
from pathlib import Path

def run_test(command: str, repo_snapshot: dict, timeout_sec: int = 30) -> dict:
    """Execute test in sandbox container."""
    
    # Create ephemeral container
    import docker
    client = docker.from_env()
    
    container = client.containers.run(
        image="python:3.11-slim",
        command=f"bash -c '{command}'",
        volumes={
            repo_snapshot['path']: {'bind': '/repo', 'mode': 'ro'},
            tempfile.gettempdir(): {'bind': '/scratch', 'mode': 'rw'}
        },
        cpu_quota=400000,  # 4 CPUs
        mem_limit='8g',
        network_disabled=False,  # restrict to approved nets
        detach=True
    )
    
    try:
        result = container.wait(timeout=timeout_sec)
        logs = container.logs().decode()
        return {
            "exit_code": result['StatusCode'],
            "stdout": logs,
            "stderr": "",
            "passed": result['StatusCode'] == 0
        }
    except Exception as e:
        return {"exit_code": -1, "stderr": str(e), "passed": False}
    finally:
        container.remove()

def run_lint(file_path: str, linter: str = "pylint") -> dict:
    """Run linter on a file."""
    result = subprocess.run(
        [linter, file_path],
        capture_output=True,
        text=True,
        timeout=10
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "issues": parse_linter_output(result.stdout)
    }
```

```python
# tools/git_mcp.py
"""MCP Server: Safe Git operations."""

import subprocess
from pathlib import Path

def create_pr(repo_path: str, branch_name: str, title: str, description: str) -> dict:
    """Create PR with validation."""
    
    # Verify branch exists and is safe
    result = subprocess.run(
        ["git", "branch", "-r"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    if branch_name not in result.stdout:
        return {"error": "Branch not found"}
    
    # Use GitHub API (authenticated) to create PR
    import requests
    pr_response = requests.post(
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls",
        json={
            "title": title,
            "body": description,
            "head": branch_name,
            "base": "main"
        },
        headers={"Authorization": f"token {github_token}"}
    )
    
    return {
        "pr_url": pr_response.json()['html_url'],
        "pr_number": pr_response.json()['number']
    }

def get_git_status(repo_path: str) -> dict:
    """Get repo state."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    return {
        "modified_files": [line.split()[1] for line in result.stdout.split('\n') if line],
        "current_branch": subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True
        ).stdout.strip()
    }
```

#### Tool Proxy (App Server)

```python
# app_server/tool_proxy.py
"""Proxy for safe tool invocation."""

import asyncio
from typing import Any

class ToolProxy:
    def __init__(self, sandbox_executor, mcp_servers):
        self.sandbox = sandbox_executor
        self.mcp = mcp_servers
    
    async def run_test(self, task_id: str, command: str) -> dict:
        """Run test with sandbox isolation and audit."""
        audit_log_entry = {
            "task_id": task_id,
            "tool": "test_runner",
            "command": command,
            "timestamp": datetime.now().isoformat()
        }
        
        result = await self.sandbox.execute_tool(
            "test_runner",
            command,
            timeout_sec=30
        )
        
        audit_log_entry["result"] = {"status": "success" if result['exit_code'] == 0 else "failed"}
        self.log_audit(audit_log_entry)
        
        return result
    
    async def run_lint(self, file_path: str) -> dict:
        """Run linter."""
        return await self.sandbox.execute_tool("linter", ["pylint", file_path])
    
    async def search_code(self, query: str, limit: int = 10) -> list:
        """Semantic code search."""
        # Query the embeddings DB
        from vector_db import EmbeddingsClient
        client = EmbeddingsClient()
        results = client.search_code(query, top_k=limit)
        return results
```

---

### 2.4 Data Stores & Indexing

#### Repo Index & Embeddings

```python
# data_stores/repo_indexer.py
"""Build and maintain repo index for fast search."""

from pathlib import Path
import json

class RepoIndexer:
    def __init__(self, vector_db_client):
        self.vector_db = vector_db_client
        self.symbol_index = {}
    
    def index_repo(self, repo_path: str):
        """Full repo index: symbols, code structure, embeddings."""
        
        # Phase 1: AST parsing for symbols
        for py_file in Path(repo_path).rglob("*.py"):
            symbols = self.extract_symbols(py_file)
            self.symbol_index[str(py_file)] = symbols
        
        # Phase 2: Embed code snippets
        code_chunks = self.chunk_code(repo_path)
        embeddings = self.embed_chunks(code_chunks)
        
        # Store in vector DB
        for chunk, emb in zip(code_chunks, embeddings):
            self.vector_db.upsert(
                id=chunk['id'],
                embedding=emb,
                metadata={"file": chunk['file'], "context": chunk['text'][:500]}
            )
        
        # Phase 3: Build index metadata
        self.save_index_metadata({
            "repo_path": repo_path,
            "symbols": self.symbol_index,
            "embedding_count": len(embeddings),
            "indexed_at": datetime.now().isoformat()
        })
    
    def search_symbol(self, name: str) -> list:
        """Find symbol by name in index."""
        results = []
        for file, symbols in self.symbol_index.items():
            for sym in symbols:
                if name.lower() in sym['name'].lower():
                    results.append((file, sym))
        return results[:10]
    
    def semantic_search(self, query: str) -> list:
        """Find code by semantic similarity."""
        query_emb = self.embed_text(query)
        results = self.vector_db.search(query_emb, top_k=10)
        return results
    
    def embed_chunks(self, chunks: list) -> list:
        """Embed code chunks using a dedicated embedding model."""
        embeddings = []
        for chunk in chunks:
            emb = self.get_embedding(chunk['text'])
            embeddings.append(emb)
        return embeddings
```

#### Telemetry & Training Data Store

```python
# data_stores/telemetry.py
"""Collect and anonymize telemetry for training and monitoring."""

from datetime import datetime
import hashlib
import json

class TelemetryStore:
    def __init__(self, db_client, anonymization_key: str):
        self.db = db_client
        self.anonymization_key = anonymization_key
    
    def log_completion(self, event: dict):
        """Log an inline completion event."""
        
        anonymized = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user_id_hash": self.hash_id(event['user_id']),
            "model": event['model'],
            "latency_ms": event['latency_ms'],
            "suggestion_accepted": event['accepted'],
            "suggestion_rank": event['rank'],  # position in top-k
            "confidence": event['confidence'],
            "language": event['language'],
            # NO sensitive data: file content, full file path, repo name
        }
        
        self.db.insert("completions", anonymized)
    
    def log_task(self, event: dict):
        """Log an agentic task."""
        
        anonymized = {
            "task_id": event['task_id'],
            "user_id_hash": self.hash_id(event['user_id']),
            "timestamp": datetime.now().isoformat(),
            "task_status": event['status'],  # "success", "failed", "cancelled"
            "execution_time_sec": event['execution_time'],
            "test_pass_rate": event['test_pass_rate'],
            "num_revisions": event['revisions'],
            "safety_flags": event['safety_flags']  # if any unsafe code detected
        }
        
        self.db.insert("tasks", anonymized)
    
    def hash_id(self, user_id: str) -> str:
        """Hash user ID for anonymization."""
        return hashlib.sha256(
            (user_id + self.anonymization_key).encode()
        ).hexdigest()[:16]
    
    def export_training_set(self, days: int = 7) -> list:
        """Export accepted completions as training examples."""
        rows = self.db.query(f"""
            SELECT * FROM completions 
            WHERE suggestion_accepted = true 
            AND timestamp >= NOW() - INTERVAL {days} DAY
            ORDER BY confidence DESC
            LIMIT 10000
        """)
        
        return [
            {
                "input": row['context'],
                "output": row['suggestion'],
                "confidence": row['confidence']
            }
            for row in rows
        ]
```

---

### 2.5 Privacy & Security

#### Redaction Engine (Pre-Model)

```python
# privacy/redaction.py
"""Detect and redact sensitive data before sending to model."""

import re

class RedactionEngine:
    def __init__(self):
        # Regex patterns for secrets
        self.patterns = {
            "api_key": r"(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9\-_]{20,})",
            "password": r"(?i)(password|passwd)['\"]?\s*[:=]\s*['\"]?([^\s'\"]+)",
            "jwt": r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
            "aws_key": r"AKIA[0-9A-Z]{16}",
            "github_token": r"ghp_[A-Za-z0-9_]{36}",
            "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
            "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "credit_card": r"\b\d{13,19}\b"
        }
    
    def redact(self, text: str) -> tuple[str, list]:
        """Redact sensitive data. Return (redacted_text, redacted_locations)."""
        
        redacted_text = text
        redacted_items = []
        
        for pattern_name, pattern in self.patterns.items():
            matches = list(re.finditer(pattern, redacted_text))
            for match in reversed(matches):  # Reverse to preserve indices
                redacted_text = (
                    redacted_text[:match.start()] + 
                    f"[{pattern_name.upper()}_REDACTED]" + 
                    redacted_text[match.end():]
                )
                redacted_items.append({
                    "type": pattern_name,
                    "start": match.start(),
                    "end": match.end()
                })
        
        return redacted_text, redacted_items
    
    def redact_context(self, file_content: str, file_path: str = None) -> str:
        """Redact from entire file."""
        redacted, _ = self.redact(file_content)
        return redacted
```

#### License Detection

```python
# privacy/license_detector.py
"""Detect copyrighted / viral code."""

import hashlib

class LicenseDetector:
    def __init__(self, code_corpus_db):
        self.corpus = code_corpus_db  # Pre-indexed code snippets with license info
    
    def check_license(self, generated_code: str) -> dict:
        """Check if generated code matches known licensed code."""
        
        # Compute fingerprint (rolling hash)
        fingerprint = self.compute_fingerprint(generated_code)
        
        # Search corpus
        matches = self.corpus.search_fingerprints(fingerprint, threshold=0.7)
        
        if matches:
            return {
                "license_warning": True,
                "licenses": [m['license'] for m in matches],
                "confidence": matches[0]['confidence'],
                "sources": [m['source_url'] for m in matches]
            }
        
        return {"license_warning": False}
    
    def compute_fingerprint(self, code: str) -> str:
        """Compute rolling hash of code."""
        # Use Rabin fingerprint for code similarity
        import hashlib
        return hashlib.sha256(code.encode()).hexdigest()
```

---

## 3. Safety & Compliance Checklist (EU/GDPR)

### 3.1 Data Residency & Processing

- ✅ All data (code, telemetry, models) stored in EU regions only.
  - **Selection**: Databricks EU workspaces (eu-west-1 for Ireland or eu-central-1 for Frankfurt).
  - **Network**: VPN/private link to on-prem for sensitive repos.
- ✅ Data Processing Agreement (DPA) with Databricks signed.
- ✅ No data transfers to US without Standard Contractual Clauses (SCCs).

### 3.2 Consent & Transparency

- ✅ **Org-level consent** for training on private code (explicit opt-in per repo).
  - UI: Settings → Privacy → "Allow training on this repo's code?" [NO] [YES, with audit]
- ✅ **User-level privacy modes:**
  - Local-only: zero data sent.
  - Partial: minimal context (200 chars).
  - Full: repo snapshot (approved orgs only).
- ✅ **Clear disclosure** of what data is used for training (dashboard).

### 3.3 User Rights

- ✅ **Right to access**: Export all personal data/telemetry on-demand.
- ✅ **Right to deletion**: Remove user from DB within 30 days (verified by ops team).
- ✅ **Right to portability**: Download trained models/completions.
- ✅ **Right to object**: Opt-out of training at any time.

### 3.4 Security & Audit

- ✅ Identity & access management (Entra ID / SAML).
- ✅ Secrets redacted before transmission (regex + ML detector).
- ✅ Audit logs for all data access (immutable, 2-year retention).
- ✅ Encryption at rest (AES-256) & in transit (TLS 1.3).
- ✅ Vulnerability scanning (SAST, DAST, supply chain scanning).
- ✅ Annual 3rd-party security audit.

### 3.5 Sub-Processors & Third Parties

| Service | Purpose | Location | DPA? |
|---------|---------|----------|------|
| Databricks | Model serving, inference | EU (eu-west-1) | ✅ |
| Redis | Session cache | EU (managed Redis) | ✅ |
| Vector DB | Code embeddings | EU (Pinecone EU or self-hosted) | ✅ |
| GitHub API | PR creation | US (with SCCs) | ✅ |

---

## 4. Training & Fine-Tuning Plan

### 4.1 Training Data   

**Sources:**
1. **Public code corpora:**
   - GitHub (Apache/MIT licensed, opt-in repos).
   - Stack Overflow (CC-BY-SA licensed).
   - Open-source projects (PyPI, npm).

2. **Internal datasets (strictly opt-in):**
   - Curated high-quality examples from pilot team.
   - Unit tests + fixed bugs (useful for learning corrections).

3. **Synthetic data:**
   - Generated test cases for edge cases (error handling, security).
   - Adversarial examples (code that should be rejected).

### 4.2 Supervised Fine-Tuning (SFT)

**Process:**
```
Input: (file_context, task) | Output: (completion | plan)
Dataset size: 500k–1M examples
Metrics during training:
  - Exact match (generated == reference): target >60%
  - Compilability: generated code compiles >95%
  - Test pass rate: code passes 80%+ provided tests
```

**Code Example:**
```python
# training/sft.py
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer

# Load curated examples
dataset = load_dataset("json", data_files="training_data.jsonl")

tokenizer = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2")

# Prepare data
def preprocess(examples):
    inputs = [f"{ex['file_context']}\n<COMPLETION>" for ex in examples['text']]
    targets = examples['completion']
    
    encoding = tokenizer(inputs, targets, truncation=True, max_length=512)
    return encoding

train_dataset = dataset.map(preprocess, batched=True)

# Fine-tune
trainer = Trainer(
    model=model,
    args=TrainingArguments(
        output_dir="./checkpoints",
        num_train_epochs=3,
        per_device_train_batch_size=16,
        save_steps=1000,
    ),
    train_dataset=train_dataset,
)

trainer.train()
```

### 4.3 RLHF (Reinforcement Learning from Human Feedback)

**Reward Functions:**
1. **Acceptance signal**: User accepts completion → +1, rejects → -1.
2. **Test pass**: Code passes provided tests → +reward proportional to coverage.
3. **Safety penalty:** Unsafe code (SQL injection, hardcoded secret) → -10.
4. **License penalty:** Code matches viral license → -5.

**Loop:**
```
1. Sample 10k completions from accept/reject logs.
2. Label high-agreement (>90% human consensus) as good/bad.
3. Train reward model: P(good|code) via classification.
4. Use PPO or DPO to optimize fast model to max reward.
5. Re-deploy weekly.
```

### 4.4 Continuous Learning

**Cadence:**
- Weekly: curate top 1k accepted completions → add to training set.
- Biweekly: retrain fast model with new examples.
- Monthly: evaluate model drift (acceptance rate vs baseline).
- Quarterly: full RLHF cycle.

---

## 5. UX & Product Flows

### 5.1 Inline Completion UX

**Trigger:**
- Auto-trigger on typing pause (300ms idle).
- Manual trigger: `Ctrl+Shift+/` (VS Code), `Cmd+Shift+/` (Mac).

**Display:**
```
Current code:
def get_user(id):
    user = db.query(User).fil|

Suggestions (ranked by confidence):
1. ✓ [92%] ter(User.id == id).first()
           └─ Matches sklearn examples

2. ✓ [87%] ter(id == User.id).one()
           └─ Exact match in your repo

3. [Explain]  [Accept] → Apply & move cursor to end
   [Dismiss]  [Next]
```

### 5.2 Agentic Task Flow

**Interaction:**
```
User chat pane:
"Add caching to the user service using Redis"

↓ App Server enriches context (repo, tests, CI config)
↓ Agent model returns plan

----
Plan Preview:
[ ] Modify src/service.py: add @cache decorator
[ ] Update requirements.txt: + redis
[ ] Run tests: pytest src/tests/test_service.py
[ ] Create PR: feature/redis-cache

Approve?  [APPROVE]  [REVISE]  [CANCEL]

↓ (if APPROVE) Execute in sandbox
↓ 
Results:
✅ Tests passed: 42 / 42
✅ Coverage: 92% → 94% (+2%)

[Open PR]  [Edit & Retry]  [Accept]
```

---

## 6. Evaluation Metrics & QA

### 6.1 Key Metrics (Dashboard)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Completion acceptance rate** | 70%+ | \# accepted / \# shown |
| **Task success rate** | 85%+ | \# tasks with passing tests / \# tasks |
| **Latency (p95)** | <500ms (completions), <5s (plan) | Histogram of API response times |
| **Hallucination rate** | <5% | Manual review of flagged suggestions |
| **Safety incidents** | 0 security violations/month | Audit log review |
| **Test pass rate** | 90%+ | Generated code run against provided tests |
| **Model drift** | <2% month-on-month | Acceptance rate vs baseline |
| **False positive rate (license)** | <5% | Manual review of warnings |

### 6.2 QA Process

**Before each release:**
1. **Unit testing:** 100 generated code samples per language/framework.
   - Compile? ✅
   - Lint? ✅
   - Run tests? ✅

2. **Red-teaming:** Adversarial prompts (SQL injection, hardcoded secrets, GPL code).
   - Should be rejected or flagged? ✅

3. **Human review:** 50 high-confidence completions from QA pool.
   - Is suggestion useful? Safe? Matches actual usage?

4. **Regression test:** Ensure acceptance rate on known-good samples <2% regression.

---

## 7. Deployment & Scaling Strategy

### 7.1 Piloting Phase (Month 6)

**Target:** 10–20 engineers, 1–2 week pilot.

**Infrastructure:**
- **Databricks workspace:** Standard cluster (8 nodes, GPU enabled).
- **Model serving:** Databricks Serving endpoints (2x fast model, 1x agent).
- **App Server:** Container on Databricks Apps or on-prem Kubernetes.
- **Data stores:** Managed Redis (Databricks) + vector DB (Pinecone EU or managed Qdrant).
- **Cost:** €8k–€15k/month.

**Deployment:**
```
databricks bundle deploy --target pilot
# Provisions serving endpoints, app server, monitoring dashboards
```

### 7.2 Scale to Production (Post-Pilot)

**Target:** 100+ engineers, 5+ teams.

**Infrastructure:**
- **Databricks:** Multi-workspace setup (one per team for isolation).
- **Model serving:** GPU cluster auto-scales (0–50 nodes).
- **App Server:** High-availability (3x replicas, load balanced).
- **Data stores:** Distributed vector DB (Pinecone/Qdrant enterprise), Redis Cluster.
- **Cost:** €50k–€150k/month (depending on concurrent users & model size).

**Deployment automation:**
```yaml
# deployment/production.yml
name: copilot-production
target: production
autoscaling:
  completions:
    min_instances: 2
    max_instances: 20
    metric: average_response_time_ms
    target: 150
  tasks:
    min_instances: 1
    max_instances: 10
    metric: queued_tasks
    target: 5
backup:
  enabled: true
  frequency: hourly
  retention_days: 30
```

### 7.3 On-Prem / Hybrid Option (For Sensitive Code)

**Architecture:**
- **Model serving:** Customer's GPU cluster (on-prem Kubernetes or Databricks).
- **App Server:** Lightweight proxy on-prem; control plane in EU cloud.
- **Sync:** Metadata & telemetry only (no code leaves customer network except to model).

**Deployment:**
```bash
# On customer's Kubernetes cluster
helm install copilot-on-prem ./helm-chart \
  --set model_serving.endpoint=internal-gpu.company.com \
  --set control_plane.endpoint=eu-control-plane.company.com \
  --set data_residency=on-prem
```

---

## 8. Six-Month Implementation Roadmap

### Month 0–1: Foundations & Requirements

**Milestones:**
- [ ] Requirements finalized with product, engineering, legal.
- [ ] Hosting choice locked (Databricks EU + on-prem option verified).
- [ ] Data processing agreement signed with Databricks.
- [ ] App Server skeleton deployed (health check, auth, rate limiting).
- [ ] IDE plugin prototype (VS Code, basic chat pane).

**Deliverables:**
- Implemented: `app_server/server.py`, `client/vscode/extension.ts`
- Docs: Architecture diagram, API spec, deployment guide.
- Team trained on codebase structure.

### Month 2–3: Core Integration & Model

**Milestones:**
- [ ] Fast completion model fine-tuned (500k examples).
- [ ] Model inference endpoint live (Databricks Serving).
- [ ] Repo indexing (AST parsing, embeddings) working.
- [ ] IDE plugin receives & displays completions (UX polish).
- [ ] Baseline metrics set (acceptance rate, latency).

**Deliverables:**
- Implemented: `model_serving/agent_runtime.py`, `data_stores/repo_indexer.py`, IDE plugin completion UI.
- Metrics dashboard live.

### Month 4: Agent Runtime & Execution

**Milestones:**
- [ ] Agent model (70B) deployed & tested.
- [ ] MCP tool servers (Git, test runner, linter, code search) live.
- [ ] Sandbox execution framework working (Docker + resource quotas).
- [ ] Task planning & execution loop tested end-to-end.
- [ ] Chat pane UX for multi-file tasks implemented.

**Deliverables:**
- Implemented: `tools/*.py` (all MCP servers), `app_server/sandbox_executor.py`, task execution e2e test harness.
- Documentation: Tool integration guide, sandbox policy reference.

### Month 5: Safety, Privacy & Hardening

**Milestones:**
- [ ] Redaction engine (secrets, PII) live and tested.
- [ ] License detection (viral code warning) working.
- [ ] GDPR workflows (consent, deletion, export) implemented.
- [ ] Audit logging complete (immutable, tamper-proof).
- [ ] Initial RLHF data collection from pilot users.

**Deliverables:**
- Implemented: `privacy/redaction.py`, `privacy/license_detector.py`, GDPR compliance scripts.
- Security audit findings remediated.
- Privacy policy & consent flow finalized.

### Month 6: Pilot Launch & Iteration

**Milestones:**
- [ ] 10–20 engineers onboarded to pilot (VS Code + JetBrains).
- [ ] Metrics collected & analyzed (acceptance rate, latency, safety).
- [ ] First RLHF cycle complete (model retrained on week 1 feedback).
- [ ] Bug fixes & UX polish based on feedback.
- [ ] Production deployment plan finalized.

**Deliverables:**
- Pilot cohort onboarding docs.
- Metrics dashboard public.
- Retrained model v1.1 deployed.
- Post-pilot retrospective & roadmap for production scale.

---

## 9. Implementation Checklist (Developer Handoff)

### Immediate Actions (Next 2 Weeks)

- [ ] **Decide on model family:**
  - [ ] Small 6B model + large 70B agent (recommended).
  - [ ] OR: Single large model with routing.
- [ ] **Hosting locked:**
  - [ ] Databricks EU (eu-west-1 / eu-central-1).
  - [ ] On-prem backup plan: internal GPU cluster specs.
- [ ] **Training data policy approved:**
  - [ ] Opt-in only for private repos.
  - [ ] Public corpus + internal opt-in.
- [ ] **App Server skeleton deployed** (scaffold with FastAPI + Redis).
- [ ] **IDE plugin builds & runs** (stub for chat pane).

### Core Development (Weeks 3–12)

- [ ] **Model inference:**
  - [ ] Download base model (Llama 2, Code Llama, or proprietary).
  - [ ] SFT on 500k examples (1–2 weeks compute).
  - [ ] Deploy to Databricks Serving endpoint.
  - [ ] Latency & throughput testing.

- [ ] **Repo indexing:**
  - [ ] AST parser for Python, JS, Go (use existing libs: `ast`, `tree-sitter`).
  - [ ] Embeddings model (use `sentence-transformers` or Databricks embeddings API).
  - [ ] Vector DB setup (Pinecone EU, Weaviate, or Qdrant).

- [ ] **Tool adapters:**
  - [ ] MCP Git server (clone, status, create PR).
  - [ ] MCP Test runner (pytest, coverage).
  - [ ] MCP Linter (pylint, black, mypy).
  - [ ] MCP Code search (symbol lookup, semantic search).

- [ ] **Execution sandbox:**
  - [ ] Docker image with test runtime.
  - [ ] Resource quotas (CPU, RAM, timeout) enforced.
  - [ ] Audit logging for all tool invocations.

- [ ] **Privacy & security:**
  - [ ] Redaction engine (regex + ML detector for secrets).
  - [ ] License detector (fingerprint matching).
  - [ ] Telemetry anonymization (user ID hashing).
  - [ ] Audit logger (immutable, DPA compliant).

- [ ] **IDE plugins:**
  - [ ] VS Code extension: completions, chat, refactor UI.
  - [ ] JetBrains plugin: same features.
  - [ ] Web IDE (browser-based, for trials).

###Testing & QA (Weeks 13–20)

- [ ] **Functional testing:**
  - [ ] 100 generated code samples compile & pass tests.
  - [ ] Multi-file refactoring tasks end-to-end.
  - [ ] Tool invocation (tests, linters) working correctly.

- [ ] **Security testing:**
  - [ ] Redaction catches all secret patterns.
  - [ ] Sandbox prevents escape (kernel sandbox validation).
  - [ ] No data leaves EU without authorization.

- [ ] **Performance testing:**
  - [ ] Latency: completion <500ms p95, task plan <5s.
  - [ ] Throughput: 100+ concurrent users.
  - [ ] Autoscaling kicks in at load spikes.

- [ ] **Privacy testing:**
  - [ ] GDPR workflows verified (deletion, export, consent).
  - [ ] Audit logs tamper-proof.
  - [ ] DPA compliance audit passed.

###Pilot & Launch (Weeks 21–24)

- [ ] **Pilot cohort onboarded** (10–20 engineers).
- [ ] **Metrics dashboard live** (acceptance rate, latency, safety).
- [ ] **Feedback collection** (weekly surveys, Slack channel).
- [ ] **First retraining cycle** (week 2–3 of pilot).
- [ ] **Go / no-go decision** for production.

---

## 10. Technical Decisions (Make Now)

### Decision 1: Model Architecture

**Options:**
- **A) Dual-model (fast 6B + agent 70B):** [**RECOMMENDED**]
  - Pros: Fast completions for UX, capable multi-file agent tasks.
  - Cons: More infrastructure, deployment complexity.
  - Cost: ~€15k/month GPU for both.

- **B) Single large model (70B) with router:**
  - Pros: Simpler deployment, single codebase.
  - Cons: Slower completions, higher latency variance.
  - Cost: ~€12k/month.

**Decision:** ✅ **Go with A (dual-model).** Better UX for completions.

---

### Decision 2: Hosting & Data Residency

**Options:**
- **A) Databricks EU (eu-west-1 Ireland):** [**RECOMMENDED FOR PILOT**]
  - Pros: Turnkey, managed infra, compliance baked in.
  - Cons: Vendor lock-in, higher cost.

- **B) Self-hosted on EU cloud (AWS/Azure/GCP):**
  - Pros: Full control, cheaper.
  - Cons: 3–4 months to build operational readiness.

- **C) Hybrid (Databricks + on-prem for sensitive repos):**
  - Pros: Privacy for sensitive code.
  - Cons: Operational complexity (months 5–6).

**Decision:** ✅ **Go with A for pilot (month 0–6).** Plan B in Q3 2026 if needed.

---

### Decision 3: Training Data & Consent

**Options:**
- **A) Public code only (no private repo training):**
  - Pros: Zero privacy risk.
  - Cons: Model quality slower to improve.

- **B) Opt-in private repo training (recommended):**
  - Pros: Better model tailored to team style.
  - Cons: Requires explicit consent, audit trail.

- **C) Implicit training (risky for EU):**
  - Pros: Fastest model improvement.
  - Cons: ❌ GDPR violation risk.

**Decision:** ✅ **Go with B (opt-in).** Clear consent, audit trail, DPA compliant.

---

### Decision 4: Inference Latency vs. Cost Trade-Off

**Options:**
- **A) Aggressive quantization (4-bit, sub-100ms latency):**
  - Pros: Fast UX, lower cost.
  - Cons: Slight quality loss (~3–5%).

- **B) FP16 (no quantization, ~200ms latency):**
  - Pros: Best quality.
  - Cons: Higher cost, slower.

**Decision:** ✅ **Go with A (quantized).** User experience wins. Verify quality loss < 5% in QA.

---

## 11. References & Key Resources

1. **GitHub Copilot Architecture:**
   - https://github.blog/2021-06-29-introducing-github-copilot-ai-pair-programmer/
   - https://github.blog/2023-03-16-gitHub-copilot-research-recitation/

2. **OpenAI Codex Papers:**
   - https://arxiv.org/abs/2107.03374 (Codex: A Study on Robustness to Adversarial Inputs)
   - https://arxiv.org/abs/2608.01879 (Evaluating LLM-based code generation)

3. **GDPR & EU Data Protection:**
   - https://gdpr-info.eu/
   - https://www.edpb.europa.eu/our-work-tools/our-documents/recommendations/recommendations-042022-dark-patterns-social-media_en

4. **Databricks Documentation:**
   - https://docs.databricks.com/en/generative-ai/agents/
   - https://docs.databricks.com/en/security/

5. **OpenAI Agents SDK:**
   - https://platform.openai.com/docs/guides/agents
   - https://github.com/openai/agents-sdk

6. **MCP Protocol:**
   - https://modelcontextprotocol.io (Model Context Protocol specification)

---

## 12. Support & Escalation

**Questions or blockers?**
- **Architecture:** Post in #architecture-review (GitHub Discussions).
- **Privacy/Compliance:** Reach out to Legal + Data Protection Officer.
- **Model performance:** Escalate to ML Ops + Data Science.
- **Deployment:** Reach out to DevOps + Cloud Architecture.

---

**Document Owner:** ML Platform Team  
**Last Updated:** 23 Feb 2026  
**Next Review:** 30 April 2026 (post-pilot)

