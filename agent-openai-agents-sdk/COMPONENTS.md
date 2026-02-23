# Component Specifications
**Copilot-Style Coding Agent - Detailed Component Design**
**Date: February 23, 2026**

---

## Table of Contents

1. [Client Layer (IDE Plugins)](#1-client-layer-ide-plugins)
2. [App Server](#2-app-server)
3. [Model Serving & Agent Runtime](#3-model-serving--agent-runtime)
4. [Execution Sandbox](#4-execution-sandbox)
5. [Data Stores & Indexing](#5-data-stores--indexing)
6. [Monitoring & Observability](#6-monitoring--observability)

---

## 1. Client Layer (IDE Plugins)

### 1.1 Overview

IDE plugins provide the primary interface for developers. They capture code context, display suggestions, and enforce privacy controls locally.

### 1.2 Supported Editors

| Editor       | Language         | Distribution        | Priority |
|--------------|------------------|---------------------|----------|
| VS Code      | TypeScript       | VS Code Marketplace | P0       |
| JetBrains    | Kotlin/Java      | JetBrains Plugin    | P1       |
| Neovim       | Lua              | Package manager     | P2       |
| Web IDE      | TypeScript       | NPM package         | P2       |

### 1.3 Core Features

#### 1.3.1 Inline Completions

**Trigger Modes**:
- **Automatic**: After typing 2+ characters or pausing for 200ms
- **Manual**: Keyboard shortcut (e.g., Ctrl+Space)
- **Ghost Text**: Display suggestion as gray inline text

**UI Components**:
```typescript
interface CompletionSuggestion {
  text: string;               // Suggested code
  range: Range;               // Position to insert
  confidence: number;         // 0.0-1.0 confidence score
  provenance?: string;        // Source attribution (license, repo)
  multiline: boolean;         // Single vs multi-line completion
}
```

**Acceptance Actions**:
- `Tab`: Accept full suggestion
- `Ctrl+Right`: Accept word-by-word
- `Esc`: Reject and hide
- `Ctrl+Click`: Show explanation modal

#### 1.3.2 Chat Pane

**Features**:
- Natural language queries (e.g., "Explain this function")
- Multi-turn conversations with context retention
- Code block rendering with syntax highlighting
- Action buttons: "Apply to file", "Copy", "Explain more"

**UI Layout**:
```
┌─────────────────────────────────────────┐
│  Copilot Assistant                      │
│  ┌───────────────────────────────────┐  │
│  │ User: How do I parse JSON in Go? │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ Assistant: Use encoding/json...   │  │
│  │ ```go                             │  │
│  │ import "encoding/json"            │  │
│  │ ...                               │  │
│  │ ```                               │  │
│  │ [Apply] [Copy] [Explain]          │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ Type your question...              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

#### 1.3.3 Multi-File Refactor UI

**Workflow**:
1. User issues command: "Refactor UserService to use caching"
2. Agent generates plan: List of files to modify, tests to update
3. Plugin shows **Plan Review Modal**:
   ```
   ┌─────────────────────────────────────────────────┐
   │  Proposed Changes (5 files)                      │
   │  ☑ src/services/user_service.py (23 lines)      │
   │  ☑ src/cache/redis_cache.py (new file)          │
   │  ☑ tests/test_user_service.py (10 lines)        │
   │  ☑ requirements.txt (1 line)                     │
   │  ☑ config/settings.py (5 lines)                  │
   │                                                  │
   │  Estimated time: ~30 seconds                     │
   │  Tests will run automatically                    │
   │                                                  │
   │  [Review Diffs] [Approve] [Cancel]               │
   └─────────────────────────────────────────────────┘
   ```
4. User reviews diffs, approves
5. Agent executes in sandbox, shows results
6. User can accept all, reject all, or cherry-pick changes

#### 1.3.4 Privacy Controls

**Settings Panel**:
```
┌─────────────────────────────────────────────┐
│  Copilot Privacy Settings                   │
│                                             │
│  Data Transmission Mode:                    │
│  ◉ Local Only (no network, limited context) │
│  ○ Partial (active file only)               │
│  ○ Full (repo-wide context)                 │
│                                             │
│  ☑ Redact secrets (API keys, tokens)        │
│  ☑ Exclude files matching .gitignore        │
│  ☑ Warn on public code matches              │
│  ☐ Allow training on my code (opt-in)       │
│                                             │
│  Current session data: 2.3 MB               │
│  [View Data] [Delete All Data]              │
└─────────────────────────────────────────────┘
```

**Secret Redaction**:
- Regex patterns to detect API keys, passwords, tokens
- Local pre-processing before sending to server
- Visual indicator in editor when secrets detected

### 1.4 Local Caching

**Cache Hierarchy**:
1. **Completion Cache**: Recently shown suggestions (TTL: 15 minutes)
2. **Embedding Cache**: File embeddings for open documents (TTL: 1 hour)
3. **Repo Index Cache**: Symbol index, file tree (TTL: 24 hours)

**Cache Storage**:
- VS Code: Use `ExtensionContext.globalState` (SQLite-backed)
- JetBrains: Use `PropertiesComponent` or custom SQLite DB
- Neovim: JSON file in `~/.local/share/nvim/copilot-cache/`

### 1.5 API Protocol

**Communication**: Bidirectional WebSocket or gRPC streaming

**Request Example** (TypeScript):
```typescript
interface CompletionRequest {
  sessionId: string;
  context: {
    filePath: string;
    language: string;
    cursorPosition: Position;
    textBeforeCursor: string;    // Last 1000 chars
    textAfterCursor: string;     // Next 500 chars
    openFiles?: string[];        // List of open file paths
    repoSnapshot?: RepoSnapshot; // Optional, based on privacy mode
  };
  privacyMode: 'local' | 'partial' | 'full';
  maxSuggestions: number;        // Default: 3
}

interface CompletionResponse {
  requestId: string;
  suggestions: CompletionSuggestion[];
  latencyMs: number;
  cached: boolean;
}
```

### 1.6 Implementation Checklist

#### VS Code Plugin
- [ ] Set up TypeScript project with LSP integration
- [ ] Implement inline completion provider (`vscode.languages.registerInlineCompletionItemProvider`)
- [ ] Create chat pane using Webview API
- [ ] Add settings panel with privacy controls
- [ ] Implement local caching (IndexedDB or SQLite)
- [ ] WebSocket client for real-time updates
- [ ] Telemetry logging (opt-in)

#### JetBrains Plugin
- [ ] Set up Kotlin/Java project with IntelliJ Platform SDK
- [ ] Implement inline completion (`CompletionContributor`)
- [ ] Create tool window for chat pane
- [ ] Add settings page (`Configurable` interface)
- [ ] Implement local caching (PropertiesComponent)
- [ ] gRPC client for server communication
- [ ] Action handlers for refactor UI

#### Neovim Plugin
- [ ] Set up Lua plugin structure
- [ ] Integrate with LSP client for completions
- [ ] Implement chat pane (floating window or split)
- [ ] Add configuration via Lua tables
- [ ] Implement local caching (JSON files)
- [ ] HTTP/WebSocket client (use `plenary.nvim`)
- [ ] Keymaps and commands

---

## 2. App Server

### 2.1 Overview

The App Server is the central orchestration layer. It handles authentication, session management, context enrichment, tool proxying, and policy enforcement.

### 2.2 Architecture

**Stateless Frontends** (horizontally scalable):
- API Gateway (authentication, rate limiting)
- Context Enricher (repo search, embeddings lookup)
- Tool Proxy (execute tools in sandboxes)
- Policy Enforcer (privacy rules, secret redaction)

**Stateful Backend**:
- Session Store (Redis): User sessions, conversation history
- Message Queue (RabbitMQ/Kafka): Async tool execution, telemetry

### 2.3 Core Services

#### 2.3.1 API Gateway

**Responsibilities**:
- Authenticate requests (JWT tokens, OAuth 2.0)
- Rate limiting (per user, per org)
- Load balancing to backend services
- Protocol translation (HTTP/WS → gRPC)

**Tech Stack**:
- **Language**: Go (high concurrency)
- **Framework**: Gin (HTTP), Gorilla WebSocket
- **Rate Limiting**: Redis-based token bucket
- **Auth**: JWT with RS256 signing, rotate keys every 90 days

**API Endpoints**:
```go
// REST API
POST   /api/v1/completions       // Inline completion request
POST   /api/v1/chat              // Chat message
POST   /api/v1/refactor          // Multi-file refactor task
GET    /api/v1/session/:id       // Get session state
DELETE /api/v1/session/:id       // Delete session

// WebSocket
WS     /ws/completions           // Streaming completions
WS     /ws/agent                 // Agentic task updates
```

**Rate Limits**:
- Free tier: 100 req/hour per user
- Pro tier: 1,000 req/hour per user
- Enterprise: Custom limits

#### 2.3.2 Context Enricher

**Responsibilities**:
- Fetch repo index (code search, symbol definitions)
- Retrieve embeddings for semantic similarity
- Assemble context window for model
- Apply privacy filters (exclude files, redact secrets)

**Context Assembly Algorithm**:
```python
def assemble_context(request: CompletionRequest) -> ModelContext:
    context = ModelContext()

    # Priority 1: Active file and cursor
    context.add_text(request.textBeforeCursor, priority=10)
    context.add_text(request.textAfterCursor, priority=9)

    # Priority 2: Imported/referenced files
    imports = extract_imports(request.textBeforeCursor)
    for imp in imports:
        file_content = repo_index.get_file(imp)
        context.add_file(file_content, priority=8)

    # Priority 3: Recently edited files
    recent_files = session_store.get_recent_files(request.sessionId)
    for file in recent_files[:5]:
        context.add_file(file, priority=7)

    # Priority 4: Semantic search results
    if request.privacyMode == 'full':
        embeddings = embedding_db.search(request.textBeforeCursor, limit=3)
        for emb in embeddings:
            context.add_snippet(emb.text, priority=6)

    # Truncate to model's context window
    return context.truncate_to_tokens(max_tokens=8000)
```

**Tech Stack**:
- **Language**: Python or Go
- **Code Search**: Elasticsearch API client
- **Vector DB**: Qdrant client
- **Caching**: Redis for frequent file lookups

#### 2.3.3 Tool Proxy

**Responsibilities**:
- Execute tool calls from agent model (test runner, linter, git commands)
- Route tool calls to appropriate sandbox
- Collect results and return to model
- Enforce security policies (no network access, filesystem restrictions)

**Tool Registry**:
```yaml
tools:
  - name: run_tests
    command: "pytest {test_file}"
    timeout: 30s
    sandbox: python_sandbox
    capabilities: [filesystem_read, filesystem_write]

  - name: lint_code
    command: "pylint {file}"
    timeout: 10s
    sandbox: python_sandbox
    capabilities: [filesystem_read]

  - name: git_create_pr
    command: "gh pr create --title '{title}' --body '{body}'"
    timeout: 20s
    sandbox: git_sandbox
    capabilities: [network, github_api]
```

**Tool Call Flow**:
1. Model outputs: `{"tool": "run_tests", "args": {"test_file": "tests/test_user.py"}}`
2. Tool Proxy validates tool exists and user has permission
3. Proxy creates ephemeral sandbox container
4. Proxy injects code + test file into sandbox
5. Sandbox executes `pytest tests/test_user.py`
6. Proxy captures stdout/stderr, exit code
7. Proxy returns result to model: `{"status": "pass", "output": "3 passed, 0 failed"}`

**Tech Stack**:
- **Language**: Go or Rust (async, high-perf)
- **Container Runtime**: Docker API or Kubernetes Jobs API
- **Message Queue**: Kafka for async tool execution
- **Timeout Handling**: Context cancellation, hard kills after timeout

#### 2.3.4 Policy Enforcer

**Responsibilities**:
- Apply organization policies (allowed tools, max token limits)
- Redact secrets before sending to model
- Check for license violations in suggestions
- Log policy violations for audit

**Secret Redaction**:
```python
import re

SECRET_PATTERNS = [
    r'api[_-]?key[_-]?=\s*["\']([a-zA-Z0-9]{32,})["\']',  # API keys
    r'password[_-]?=\s*["\']([^"\']+)["\']',               # Passwords
    r'sk-[a-zA-Z0-9]{48}',                                # OpenAI keys
    r'ghp_[a-zA-Z0-9]{36}',                               # GitHub tokens
]

def redact_secrets(code: str) -> tuple[str, list[str]]:
    redacted_code = code
    detected_secrets = []

    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, code)
        for match in matches:
            redacted_code = redacted_code.replace(match, '<REDACTED>')
            detected_secrets.append(f'Secret type: {pattern[:20]}...')

    return redacted_code, detected_secrets
```

**License Detection**:
- Hash suggestions and compare against known code corpus
- Flag matches with confidence score
- Display warning to user if match found

**Tech Stack**:
- **Language**: Python (for regex and ML-based detection)
- **License DB**: SQLite with hashed code snippets
- **Secret Scanner**: Custom regex + ML model (e.g., trained on labeled secrets)

### 2.4 Session Management

**Session Store** (Redis):
```json
{
  "sessionId": "sess_abc123",
  "userId": "user_456",
  "createdAt": "2026-02-23T09:00:00Z",
  "lastActivity": "2026-02-23T09:28:00Z",
  "context": {
    "recentFiles": ["src/main.py", "src/utils.py"],
    "conversationHistory": [
      {"role": "user", "content": "Explain this function"},
      {"role": "assistant", "content": "This function..."}
    ]
  },
  "privacyMode": "partial",
  "metadata": {
    "requestCount": 42,
    "acceptanceRate": 0.68
  }
}
```

**TTL**: Sessions expire after 1 hour of inactivity

### 2.5 Telemetry Ingestion

**Telemetry Events**:
- `completion_requested`: User triggered completion
- `completion_shown`: Suggestions displayed to user
- `completion_accepted`: User accepted suggestion
- `completion_rejected`: User rejected or ignored
- `error_occurred`: API error, model error, timeout
- `privacy_violation`: Secret detected, license violation

**Event Schema**:
```typescript
interface TelemetryEvent {
  eventType: string;
  timestamp: string;
  sessionId: string;
  userId: string;         // Anonymized hash
  metadata: {
    latencyMs?: number;
    suggestionCount?: number;
    acceptedIndex?: number;
    errorCode?: string;
  };
}
```

**Storage**: Write to Kafka → Stream to ClickHouse or PostgreSQL for analysis

### 2.6 Deployment

**Container Image** (Dockerfile):
```dockerfile
FROM golang:1.22 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o app-server ./cmd/server

FROM alpine:latest
RUN apk --no-cache add ca-certificates
COPY --from=builder /app/app-server /usr/local/bin/
EXPOSE 8080 8081
CMD ["app-server"]
```

**Kubernetes Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app-server
  template:
    metadata:
      labels:
        app: app-server
    spec:
      containers:
      - name: app-server
        image: registry.eu.example.com/app-server:v1.0.0
        ports:
        - containerPort: 8080  # HTTP
        - containerPort: 8081  # Metrics
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: app-server-secrets
              key: redis-url
        - name: MODEL_SERVING_ENDPOINT
          value: "http://model-serving:8000"
        resources:
          requests:
            cpu: "1"
            memory: "2Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

### 2.7 Implementation Checklist

- [ ] Implement API Gateway (Go, Gin framework)
- [ ] Add JWT authentication and rate limiting
- [ ] Implement Context Enricher service
- [ ] Integrate Elasticsearch for code search
- [ ] Integrate Qdrant for vector embeddings
- [ ] Implement Tool Proxy with Docker API
- [ ] Create tool registry and validation logic
- [ ] Implement Policy Enforcer with secret redaction
- [ ] Set up Redis for session management
- [ ] Implement telemetry ingestion (Kafka producer)
- [ ] Write health check and metrics endpoints
- [ ] Dockerize and create K8s manifests
- [ ] Set up horizontal pod autoscaling

---

## 3. Model Serving & Agent Runtime

### 3.1 Overview

Model Serving provides inference APIs for two model tiers:
1. **Fast Model**: Inline completions (<500ms)
2. **Agent Model**: Multi-step tasks with tool use (1-5s)

### 3.2 Model Architecture

#### Fast Model (Tier 1)
- **Base**: CodeLlama-7B or StarCoder-3B (fine-tuned)
- **Quantization**: INT8 or FP16 for faster inference
- **Context Window**: 8K tokens
- **Batch Size**: 16-32 for throughput
- **Deployment**: 4-8 replicas on A10/T4 GPUs

#### Agent Model (Tier 2)
- **Base**: GPT-4-Turbo, Claude-3-Opus, or Mixtral-8x22B
- **Tool Training**: Fine-tuned with function calling examples
- **Context Window**: 32K tokens
- **Batch Size**: 1-4 (longer generation)
- **Deployment**: 2-4 replicas on A100/H100 GPUs

### 3.3 Inference Engine

**Options**:
1. **vLLM**: Open-source, PagedAttention, continuous batching
2. **TGI (Text Generation Inference)**: HuggingFace, supports many models
3. **TensorRT-LLM**: NVIDIA-optimized, best for A100/H100
4. **Custom**: Build on PyTorch/JAX for full control

**Recommended**: **vLLM** for ease of use and performance

**vLLM Configuration**:
```bash
# Fast Model
python -m vllm.entrypoints.openai.api_server \
  --model codellama/CodeLlama-7b-hf \
  --tensor-parallel-size 1 \
  --max-model-len 8192 \
  --port 8000

# Agent Model
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mixtral-8x22B-Instruct-v0.1 \
  --tensor-parallel-size 2 \
  --max-model-len 32768 \
  --port 8001
```

### 3.4 Agent Runtime

**Responsibilities**:
- Parse agent model output (tool calls, reasoning steps)
- Execute tool calls via Tool Proxy
- Maintain conversation state across agent steps
- Implement verification loop (run tests, check errors, retry)

**Agent Loop**:
```python
def run_agent_task(user_request: str, context: ModelContext) -> AgentResult:
    max_iterations = 5
    conversation = [{"role": "user", "content": user_request}]

    for i in range(max_iterations):
        # Get model response
        response = agent_model.generate(conversation, context)
        conversation.append({"role": "assistant", "content": response})

        # Parse tool calls
        tool_calls = parse_tool_calls(response)

        if not tool_calls:
            # No more tools, agent is done
            return AgentResult(success=True, output=response)

        # Execute tools
        tool_results = []
        for tool_call in tool_calls:
            result = execute_tool(tool_call.name, tool_call.args)
            tool_results.append(result)

        # Feed results back to model
        conversation.append({
            "role": "tool",
            "content": json.dumps(tool_results)
        })

        # Check if verification passed
        if all(r.status == "pass" for r in tool_results):
            return AgentResult(success=True, output=response, tool_results=tool_results)

    # Max iterations reached
    return AgentResult(success=False, error="Max iterations exceeded")
```

**Tool Call Format** (Function Calling):
```json
{
  "reasoning": "I need to add a test for the new caching logic",
  "tool_calls": [
    {
      "id": "call_1",
      "function": {
        "name": "create_file",
        "arguments": "{\"path\": \"tests/test_cache.py\", \"content\": \"...\"}"
      }
    },
    {
      "id": "call_2",
      "function": {
        "name": "run_tests",
        "arguments": "{\"test_file\": \"tests/test_cache.py\"}"
      }
    }
  ]
}
```

### 3.5 Model Optimization

**Quantization**:
- INT8: 50% smaller, 2x faster, minimal accuracy loss for code models
- FP16: Standard for GPUs, good balance

**Speculative Decoding**:
- Use small "draft" model to predict tokens, large model verifies
- Can achieve 2-3x speedup for long completions

**KV-Cache Reuse**:
- Cache attention keys/values for common prefixes (e.g., imports, boilerplate)
- Reduces latency for repeated context

**Batching**:
- Continuous batching (vLLM): Add requests to in-flight batches dynamically
- Increases throughput without impacting latency

### 3.6 Deployment

**Kubernetes StatefulSet** (for persistent KV-cache):
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: model-serving-fast
spec:
  serviceName: model-serving-fast
  replicas: 4
  selector:
    matchLabels:
      app: model-serving-fast
  template:
    metadata:
      labels:
        app: model-serving-fast
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:v0.3.0
        command:
          - python
          - -m
          - vllm.entrypoints.openai.api_server
          - --model
          - codellama/CodeLlama-7b-hf
          - --tensor-parallel-size
          - "1"
          - --max-model-len
          - "8192"
        ports:
        - containerPort: 8000
        resources:
          requests:
            nvidia.com/gpu: 1
          limits:
            nvidia.com/gpu: 1
        volumeMounts:
        - name: model-cache
          mountPath: /root/.cache/huggingface
  volumeClaimTemplates:
  - metadata:
      name: model-cache
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 50Gi
```

### 3.7 Model Registry

**Purpose**: Version control for models, track experiments, rollback

**Options**:
- MLflow: Open-source, good for experiments
- Weights & Biases: Commercial, excellent UI
- Custom: S3 + metadata DB

**Registry Schema**:
```json
{
  "modelId": "codellama-7b-v2-finetuned",
  "version": "1.2.3",
  "baseModel": "codellama/CodeLlama-7b-hf",
  "fineTuneData": "s3://models/finetune-dataset-v2.jsonl",
  "metrics": {
    "acceptanceRate": 0.72,
    "testPassRate": 0.85,
    "hallucinationRate": 0.08
  },
  "deployedAt": "2026-02-20T10:00:00Z",
  "status": "production"
}
```

### 3.8 Implementation Checklist

- [ ] Set up GPU cluster (K8s with NVIDIA device plugin)
- [ ] Install vLLM or TGI
- [ ] Download and test base models (CodeLlama, StarCoder)
- [ ] Implement agent runtime (Python service)
- [ ] Create tool call parser and executor
- [ ] Implement verification loop logic
- [ ] Set up model registry (MLflow)
- [ ] Create K8s manifests for model serving
- [ ] Implement health checks and readiness probes
- [ ] Set up model monitoring (latency, GPU util, errors)

---

## 4. Execution Sandbox

### 4.1 Overview

Execution Sandbox provides isolated environments for running tests, linters, and other tools on generated code. Security is paramount.

### 4.2 Architecture

**Container-Based Isolation**:
- Each tool execution runs in an ephemeral Docker container
- Strict resource limits (CPU, memory, disk, time)
- No network access by default
- Read-only filesystem except for `/workspace`

### 4.3 Sandbox Lifecycle

```
1. Tool Proxy receives tool execution request
2. Sandbox Manager creates new container from language-specific image
3. Code and dependencies injected into /workspace
4. Tool command executed (e.g., pytest, pylint)
5. Stdout/stderr captured, exit code recorded
6. Container destroyed, resources cleaned up
7. Results returned to Tool Proxy
```

**TTL**: Max execution time 60 seconds, then hard kill

### 4.4 Language-Specific Images

**Python Sandbox** (`sandbox-python:latest`):
```dockerfile
FROM python:3.11-slim
RUN pip install pytest pylint black isort mypy
RUN useradd -m -u 1000 sandbox
USER sandbox
WORKDIR /workspace
CMD ["/bin/bash"]
```

**Node.js Sandbox** (`sandbox-nodejs:latest`):
```dockerfile
FROM node:20-alpine
RUN npm install -g jest eslint prettier typescript
RUN adduser -D -u 1000 sandbox
USER sandbox
WORKDIR /workspace
CMD ["/bin/sh"]
```

**Go Sandbox** (`sandbox-go:latest`):
```dockerfile
FROM golang:1.22-alpine
RUN apk add --no-cache git
RUN adduser -D -u 1000 sandbox
USER sandbox
WORKDIR /workspace
CMD ["/bin/sh"]
```

### 4.5 Security Controls

**Network Policies**:
```bash
# No outbound network access
docker run --network none ...
```

**Resource Limits**:
```bash
docker run \
  --cpus="0.5" \
  --memory="512m" \
  --memory-swap="512m" \
  --pids-limit=100 \
  ...
```

**Filesystem**:
```bash
docker run \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  -v /path/to/workspace:/workspace:rw \
  ...
```

**Seccomp Profile**: Restrict syscalls (no `mount`, `reboot`, etc.)

### 4.6 Tool Adapters

**Test Runner**:
```python
def run_tests(test_file: str, code_files: list[str]) -> ToolResult:
    # Create temp directory
    workspace = tempfile.mkdtemp()

    # Write code files
    for file in code_files:
        write_file(f"{workspace}/{file.path}", file.content)

    # Run pytest in sandbox
    result = docker.run(
        image="sandbox-python:latest",
        command=f"pytest {test_file} -v",
        volumes={workspace: "/workspace"},
        timeout=30,
        network_mode="none"
    )

    # Parse output
    return ToolResult(
        status="pass" if result.exit_code == 0 else "fail",
        output=result.stdout,
        exitCode=result.exit_code
    )
```

**Linter**:
```python
def lint_code(file_path: str, code: str) -> ToolResult:
    workspace = tempfile.mkdtemp()
    write_file(f"{workspace}/{file_path}", code)

    result = docker.run(
        image="sandbox-python:latest",
        command=f"pylint {file_path}",
        volumes={workspace: "/workspace"},
        timeout=10,
        network_mode="none"
    )

    # Parse pylint output (warnings, errors)
    issues = parse_pylint_output(result.stdout)

    return ToolResult(
        status="warn" if len(issues) > 0 else "pass",
        issues=issues
    )
```

### 4.7 Kubernetes Jobs (Alternative to Docker API)

**Pros**: Better orchestration, resource management
**Cons**: Slower startup (~2-5s vs <1s for Docker)

**Job Template**:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: test-run-{{ .RequestID }}
spec:
  ttlSecondsAfterFinished: 300
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: sandbox
        image: sandbox-python:latest
        command: ["pytest", "/workspace/tests/test_user.py"]
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
      volumes:
      - name: workspace
        emptyDir: {}
```

### 4.8 Implementation Checklist

- [ ] Create Dockerfiles for Python, Node.js, Go, Java sandboxes
- [ ] Build and push images to container registry
- [ ] Implement Sandbox Manager service (Go/Python)
- [ ] Integrate Docker API or K8s Jobs API
- [ ] Implement resource limits and security policies
- [ ] Create tool adapters (test runner, linter, formatter)
- [ ] Implement cleanup logic (delete old containers/jobs)
- [ ] Add monitoring (sandbox usage, errors, timeouts)
- [ ] Test with malicious code (try to escape sandbox)
- [ ] Document supported tools and language versions

---

## 5. Data Stores & Indexing

### 5.1 Overview

Data stores support context retrieval, telemetry, user management, and training data collection.

### 5.2 Repo Index (Code Search)

**Purpose**: Fast search across codebase for symbols, function definitions, imports

**Technology**: Elasticsearch or Meilisearch

**Index Schema**:
```json
{
  "repoId": "repo_123",
  "filePath": "src/services/user_service.py",
  "language": "python",
  "content": "class UserService:\n    def get_user(self, user_id)...",
  "symbols": [
    {"name": "UserService", "type": "class", "line": 1},
    {"name": "get_user", "type": "method", "line": 2}
  ],
  "imports": ["flask", "sqlalchemy"],
  "lastModified": "2026-02-23T09:00:00Z"
}
```

**Indexing Process**:
1. User connects repo (GitHub, GitLab, Bitbucket)
2. Webhook triggers indexing job
3. Parse files, extract symbols, compute embeddings
4. Index in Elasticsearch and vector DB
5. Update on every commit (incremental indexing)

### 5.3 Vector DB (Embeddings)

**Purpose**: Semantic code search (find similar functions, related code)

**Technology**: Qdrant, Weaviate, or pgvector (Postgres extension)

**Vector Schema**:
```json
{
  "id": "snippet_456",
  "vector": [0.123, -0.456, ...],  // 768-dim embedding
  "metadata": {
    "repoId": "repo_123",
    "filePath": "src/utils/cache.py",
    "snippet": "def cache_result(func):\n    @wraps(func)...",
    "startLine": 10,
    "endLine": 20
  }
}
```

**Embedding Model**: CodeBERT, GraphCodeBERT, or OpenAI `text-embedding-ada-002`

**Search Example**:
```python
# User types: "how to cache function results"
query_embedding = embedding_model.encode(user_query)
results = vector_db.search(
    collection="code_snippets",
    query_vector=query_embedding,
    limit=5,
    filter={"repoId": current_repo_id}
)
```

### 5.4 Relational DB (PostgreSQL)

**Purpose**: User accounts, permissions, audit logs, org settings

**Schema**:
```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    org_id UUID REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50),  -- free, pro, enterprise
    data_residency VARCHAR(50),  -- eu, us
    settings JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Repos
CREATE TABLE repositories (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    name VARCHAR(255),
    git_url VARCHAR(500),
    indexed_at TIMESTAMP,
    settings JSONB
);

-- Audit logs
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

### 5.5 Telemetry DB (Time-Series)

**Purpose**: Store usage metrics, performance data, error logs

**Technology**: ClickHouse (fast analytics) or PostgreSQL (simpler)

**Schema** (ClickHouse):
```sql
CREATE TABLE telemetry_events (
    timestamp DateTime,
    event_type LowCardinality(String),
    session_id String,
    user_id String,
    latency_ms UInt32,
    accepted Boolean,
    error_code String,
    metadata String  -- JSON blob
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, event_type);
```

**Queries**:
```sql
-- Acceptance rate by day
SELECT
    toDate(timestamp) AS day,
    countIf(accepted) / count() AS acceptance_rate
FROM telemetry_events
WHERE event_type = 'completion_shown'
  AND timestamp >= now() - INTERVAL 7 DAY
GROUP BY day
ORDER BY day;

-- P95 latency
SELECT quantile(0.95)(latency_ms) AS p95_latency
FROM telemetry_events
WHERE event_type = 'completion_requested'
  AND timestamp >= now() - INTERVAL 1 HOUR;
```

### 5.6 Training Data Store

**Purpose**: Collect labeled examples for fine-tuning and RLHF

**Structure**:
```
s3://training-data/
  ├── supervised/
  │   ├── completions/
  │   │   └── 2026-02-23.jsonl
  │   └── refactors/
  │       └── 2026-02-23.jsonl
  ├── rlhf/
  │   ├── accepted/
  │   └── rejected/
  └── synthetic/
      ├── tests/
      └── benchmarks/
```

**JSONL Format**:
```jsonl
{"prompt": "def add_numbers(a, b):", "completion": "\n    return a + b", "accepted": true, "timestamp": "2026-02-23T09:15:00Z"}
{"prompt": "class UserService:", "completion": "\n    def __init__(self, db):\n        self.db = db", "accepted": false, "timestamp": "2026-02-23T09:16:00Z"}
```

### 5.7 Implementation Checklist

- [ ] Deploy Elasticsearch cluster (3 nodes, replication factor 2)
- [ ] Create index schema and mappings for code search
- [ ] Deploy Qdrant for vector embeddings
- [ ] Train or download code embedding model
- [ ] Set up PostgreSQL database (RDS or self-hosted)
- [ ] Create database schema (users, orgs, repos, audit logs)
- [ ] Deploy ClickHouse for telemetry (or use PostgreSQL + TimescaleDB)
- [ ] Create telemetry tables and materialized views
- [ ] Set up S3/MinIO for training data storage
- [ ] Implement data retention policies (auto-delete after 90 days)
- [ ] Create backup and restore procedures
- [ ] Set up monitoring (DB performance, disk usage, query latency)

---

## 6. Monitoring & Observability

### 6.1 Overview

Comprehensive monitoring ensures system health, model quality, and quick incident response.

### 6.2 Metrics (Prometheus)

**System Metrics**:
- `http_request_duration_seconds`: API latency (histogram)
- `http_requests_total`: Request count by endpoint, status code
- `model_inference_duration_seconds`: Model latency
- `gpu_utilization_percentage`: GPU usage
- `sandbox_execution_duration_seconds`: Tool execution time
- `cache_hit_rate`: Completion cache hit rate

**Business Metrics**:
- `completion_acceptance_rate`: % accepted suggestions
- `test_pass_rate`: % of generated code passing tests
- `hallucination_rate`: % of invalid suggestions
- `safety_incidents_total`: Count of security/license violations

**Prometheus Config**:
```yaml
scrape_configs:
  - job_name: 'app-server'
    static_configs:
      - targets: ['app-server:8081']
    scrape_interval: 15s

  - job_name: 'model-serving'
    static_configs:
      - targets: ['model-serving:8000']
    scrape_interval: 30s

  - job_name: 'sandbox-manager'
    static_configs:
      - targets: ['sandbox-manager:8082']
    scrape_interval: 15s
```

### 6.3 Logging (ELK Stack)

**Structured Logs** (JSON format):
```json
{
  "timestamp": "2026-02-23T09:28:15Z",
  "level": "info",
  "service": "app-server",
  "requestId": "req_abc123",
  "message": "Completion request processed",
  "latencyMs": 245,
  "userId": "user_456",
  "sessionId": "sess_789"
}
```

**Log Aggregation**:
- **Filebeat**: Ship logs from containers to Logstash
- **Logstash**: Parse, enrich, forward to Elasticsearch
- **Elasticsearch**: Store and index logs
- **Kibana**: Visualize, search, analyze logs

**Useful Queries**:
- Errors in last hour: `level:error AND timestamp:[now-1h TO now]`
- Slow requests: `latencyMs:>1000`
- User activity: `userId:"user_456"`

### 6.4 Tracing (Jaeger)

**Distributed Tracing**: Track requests across services (API Gateway → Context Enricher → Model Serving → Sandbox)

**Trace Example**:
```
Request ID: req_abc123
├─ API Gateway (10ms)
├─ Context Enricher (50ms)
│  ├─ Elasticsearch query (20ms)
│  └─ Qdrant search (25ms)
├─ Model Serving (200ms)
│  └─ vLLM inference (195ms)
└─ Response serialization (5ms)
Total: 265ms
```

**Instrumentation** (OpenTelemetry):
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

tracer_provider = TracerProvider()
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-agent",
    agent_port=6831,
)
tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("assemble_context")
def assemble_context(request):
    # ... code ...
```

### 6.5 Dashboards (Grafana)

**System Health Dashboard**:
- API request rate and latency (P50, P95, P99)
- Error rate (4xx, 5xx)
- GPU utilization (per node)
- Pod CPU/memory usage
- Database query latency

**Model Performance Dashboard**:
- Acceptance rate (by model version, by user)
- Test pass rate
- Hallucination rate
- Suggestion diversity (unique vs repeated suggestions)

**User Experience Dashboard**:
- Average latency per user
- Acceptance rate per user/team
- Most rejected suggestion types
- Privacy mode usage

### 6.6 Alerting (Prometheus Alertmanager)

**Alert Rules**:
```yaml
groups:
  - name: copilot_alerts
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency (P95 > 1s)"

      - alert: LowAcceptanceRate
        expr: completion_acceptance_rate < 0.3
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Acceptance rate dropped below 30%"

      - alert: SafetyIncident
        expr: increase(safety_incidents_total[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Security or license violation detected"

      - alert: ModelServingDown
        expr: up{job="model-serving"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Model serving is down"
```

**Notification Channels**:
- Slack (warnings, info)
- PagerDuty (critical alerts, on-call rotation)
- Email (daily summaries)

### 6.7 Implementation Checklist

- [ ] Deploy Prometheus server and Alertmanager
- [ ] Instrument services with Prometheus client libraries
- [ ] Create custom metrics (acceptance rate, test pass rate)
- [ ] Deploy ELK Stack (Elasticsearch, Logstash, Kibana)
- [ ] Configure log shippers (Filebeat) on all pods
- [ ] Deploy Jaeger for distributed tracing
- [ ] Instrument services with OpenTelemetry
- [ ] Create Grafana dashboards (system, model, UX)
- [ ] Configure alert rules in Prometheus
- [ ] Set up notification channels (Slack, PagerDuty)
- [ ] Test alerting (trigger alerts manually)
- [ ] Document runbooks for common incidents

---

## Summary

This document provides implementation-ready specifications for all major components:

1. **Client (IDE Plugins)**: Inline completions, chat pane, privacy controls, local caching
2. **App Server**: API gateway, context enrichment, tool proxy, policy enforcement
3. **Model Serving**: Fast and agent models, vLLM inference, agent runtime
4. **Execution Sandbox**: Container-based isolation, language-specific images, security controls
5. **Data Stores**: Code search (Elasticsearch), embeddings (Qdrant), relational (PostgreSQL), telemetry (ClickHouse)
6. **Monitoring**: Metrics (Prometheus), logs (ELK), tracing (Jaeger), dashboards (Grafana), alerting

Each section includes architecture diagrams, code examples, configuration snippets, and implementation checklists.

**Next**: Review [SECURITY.md](./SECURITY.md) for detailed privacy and security controls, then [DEPLOYMENT.md](./DEPLOYMENT.md) for infrastructure and deployment strategies.

---

**Document Version**: 1.0
**Last Updated**: February 23, 2026
**Owner**: Slovakia Engineering Team / AI Platform
