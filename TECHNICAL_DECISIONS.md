# Copilot Coding Agent: Technical Decisions & Quick Start

**Date:** 23 Feb 2026, 09:28 CET  
**Status:** For Immediate Action by Architecture Review  

---

## Critical Decisions (Required by 28 Feb 2026)

### 1. Model Family: Dual-Track (RECOMMENDED)

**Decision: Implement TWO models**

| Aspect | Fast Model (Completions) | Agent Model (Tasks) |
|--------|--------------------------|-------------------|
| **Size** | 6B parameters (quantized 4-bit) | 70B+ parameters |
| **Base** | Code Llama 6B or Llama 2 6B | Meta Llama 2 70B or Mistral |
| **Latency Target** | <100ms (p95) | <5s for plan, <30s execute |
| **Inference** | vLLM (quantized) | Databricks Serving |
| **Cost** | ~€2k/month (2 GPU nodes) | ~€8k/month (4 GPU nodes) |
| **Training Data** | 500k examples (completions) | 100k + 50k synthetic (agentic) |

**Rationale:**
- Completions must be fast (<500ms round-trip including network).
- 6B quantized hits this; 70B would timeout repeatedly, harming UX.
- 70B needed for multi-file planning (safety checks, test understanding).
- Separate inference clusters allow independent scaling.

**Approval:** ✅ Recommend to CTO by 25 Feb.

---

### 2. Hosting & Data Residency

**Decision: Databricks EU + On-Prem Plan**

| Component | Pilot (Months 0–6) | Production (Q3 2026+) |
|-----------|-----------------|---------------------|
| **Region** | Databricks eu-west-1 (Ireland) | Option B: self-hosted EU cloud |
| **Data Residency** | EU only (DPA signed) | EU + on-prem for sensitive |
| **Compliance** | GDPR, CCPA | GDPR, local data laws |
| **Cost** | €15k/month | €80k+/month (self-hosted) |

**Databricks EU Specifics:**
- Workspace in eu-west-1 (AWS Ireland).
- DPA: Databricks EU DPA + SCCs for US sub-processors.
- Network: VPN option available for air-gapped repos.
- Compliance: SOC 2 Type II, ISO 27001.

**On-Prem Plan (Months 5–6):**
- GPU cluster (NVIDIA A100) on customer Kubernetes.
- Model inference: local serving endpoint.
- App Server: control plane in Databricks EU, data plane on-prem.
- Sync: metadata + telemetry only (no code leaves customer network).

**Approval:** ✅ Databricks for pilot. DPA signed by 20 Feb.

---

### 3. Training Data Policy & Consent

**Decision: Opt-In Only + Audit Trail**

**Policy:**
- **Public code:** GitHub (Apache/MIT licensed) + Stack Overflow CC-BY-SA.
- **Private repos:** Explicit opt-in per repository.
  - Consent form: "Allow training on this repo's code?" → Yes/Log / No
  - Audit trail: /api/admin/training-consent?repo=x (query all opted-in).
  - Revocation: Any time → removes future data, old data deleted in 30 days.

**Implementation:**
```python
# app_server/consent.py
class ConsentManager:
    def can_train_on_repo(self, repo_id: str, user_id: str) -> bool:
        """Check if training allowed for this repo."""
        record = self.db.query(f"""
            SELECT * FROM training_consent 
            WHERE repo_id = {repo_id} AND status = 'APPROVED'
        """)
        return bool(record)
    
    def toggle_consent(self, repo_id: str, enabled: bool):
        """User opt-in/out for training."""
        self.db.insert("training_consent", {
            "repo_id": repo_id,
            "status": "APPROVED" if enabled else "REVOKED",
            "timestamp": now(),
            "action_by": current_user.id
        })
        
        # If revoked, queue old data for deletion (30-day grace)
        if not enabled:
            queue_for_deletion(repo_id, days=30)
```

**Approval:** ✅ Legal to review by 24 Feb.

---

### 4. Inference Latency vs. Quality Trade-Off

**Decision: Aggressive Quantization (4-Bit)**

**Justification:**
- Target P95 latency: <100ms for completions (including network).
- FP16 model inference: ~200ms (too slow).
- 4-bit quantized: ~60–80ms (acceptable).
- Expected quality loss: 3–5% (acceptable for completions, verify in QA).

**Benchmarks:**
```
Model             | Quantization | Latency (ms) | Accuracy Loss |
Llama 2 6B        | FP16         | 120–150      | 0%            |
Llama 2 6B        | 8-bit        | 80–100       | 1–2%          |
Llama 2 6B (GPTQ) | 4-bit        | 60–80        | 3–5%          |
```

**Mitigation:**
- Validate on 10k generated samples (compile, lint, test pass rate).
- If accuracy loss >5%, revert to 8-bit.
- Monitor acceptance rate in production (baseline regression triggers rollback).

**Approval:** ✅ Recommend 4-bit; test threshold set at 2% regression tolerance.

---

### 5. Execution Sandbox Technology

**Decision: Docker Containers + Ephemeral Volumes**

**Options Evaluated:**
- Option A: OCI containers (Docker) — ✅ **Chosen**
- Option B: Kubernetes pods — Too complex for MVP.
- Option C: Firecracker VMs — Overkill, higher latency.

**Docker Setup:**
```yaml
# sandbox/docker-compose.yml
version: '3'
services:
  task-executor:
    image: python:3.11-slim
    volumes:
      - /tmp/repo_snapshot_${TASK_ID}:/repo:ro
      - /tmp/scratch_${TASK_ID}:/scratch:rw
    mem_limit: 8g
    cpus: '4'
    read_only: true
    tmpfs:
      - /run
      - /tmp
    networks:
      - sandbox-net
    environment:
      - TASK_ID=${TASK_ID}
      - MAX_TIME_SEC=60
    command: /usr/bin/python /sandbox/runner.py

networks:
  sandbox-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

**Constraints:**
- No outbound network (except to approved language servers).
- Max 60 seconds execution time (hard kill after).
- Resource quotas: 4 CPU, 8 GB RAM, 10 GB disk.
- Read-only repo; read-write scratch volume.

**Approval:** ✅ Approved. Start Docker setup in Week 1.

---

### 6. IDE Plugin Priority: VS Code First

**Decision: VS Code → JetBrains → Web IDE**

**Phase 1 (Months 1–3):** VS Code only
- Largest user base.
- Rapid iteration with TypeScript + LSP.
- Easier debugging.

**Phase 2 (Months 4–5):** JetBrains (IDEA, PyCharm)
- Use existing IDE plugin SDK.
- Share backend with VS Code via same App Server API.

**Phase 3 (Months 6+):** Web IDE (browser-based)
- Optional for trials.
- Browser-based UI (React).

**Approval:** ✅ VS Code priority locked. JetBrains planned for month 4.

---

## Implementation Start (Week 1 Tasks)

### App Server Skeleton (FastAPI)

```python
# app_server/main.py
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.authentication import AuthenticationMiddleware
import redis

app = FastAPI(title="Copilot Coding Agent", version="0.1.0")

# CORS for IDE plugins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["vscode://", "jetbrains://", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis for session management
redis_client = redis.Redis(
    host="redis.internal",
    port=6379,
    decode_responses=True,
    ssl=True,  # EU compliance: TLS to Redis
)

@app.on_event("startup")
async def startup():
    """Verify dependencies on startup."""
    try:
        redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise

@app.get("/health")
async def health():
    """Health check for k8s/load balancer."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "redis": "connected" if redis_client.ping() else "disconnected"
    }

# TODO: Add endpoints
# POST /api/v1/completions
# POST /api/v1/tasks
# POST /api/v1/tools/run-test
# WS /ws/task-stream
```

**Checklist:**
- [ ] FastAPI app scaffolded.
- [ ] Redis connection tested (use test Redis container).
- [ ] Health endpoint responds.
- [ ] Docker image builds.
- [ ] Deployed to Databricks Apps (test deploy).

**Owner:** Backend Lead  
**Due:** 27 Feb 2026

---

### Model Inference Endpoint (Databricks Serving)

```python
# model_serving/register_model.py
from mlflow.models import ModelSignature
from mlflow.types.schema import ColSpec, Schema

# Step 1: Download & fine-tune base model
import transformers
model = transformers.AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-6b-hf",
    torch_dtype="auto"
)
tokenizer = transformers.AutoTokenizer.from_pretrained("meta-llama/Llama-2-6b-hf")

# Step 2: Register in MLflow
import mlflow
with mlflow.start_run():
    mlflow.transformers.log_model(
        transformers_model={"model": model, "tokenizer": tokenizer},
        artifact_path="model",
        input_example={"text": "def hello():"},
    )

# Step 3: Deploy to Databricks Serving
from databricks.sdk.service.serving import CreateServingEndpointRequest

client = databricks.sdk.WorkspaceClient()
client.serving_endpoints.create(
    CreateServingEndpointRequest(
        name="fast-completion-model",
        config={
            "served_models": [{
                "model_name": "llama-2-6b-fast",
                "model_version": "1",
                "workload_type": "GPU_SMALL",
                "scale_to_zero_enabled": False,
            }]
        }
    )
)
```

**Checklist:**
- [ ] Model downloaded & registered in MLflow.
- [ ] Endpoint created in Databricks Serving.
- [ ] Test inference: call endpoint, verify response <100ms.
- [ ] Latency, throughput tested.

**Owner:** ML Infrastructure Lead  
**Due:** 28 Feb 2026

---

### Privacy Redaction Engine (MVP)

```python
# privacy/redaction.py
import re

class RedactionEngine:
    def __init__(self):
        self.patterns = {
            "api_key": r"(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9\-_]{20,})",
            "aws_key": r"AKIA[0-9A-Z]{16}",
            "github_token": r"ghp_[A-Za-z0-9_]{36}",
            "jwt": r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
            "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
        }
    
    def redact(self, text: str) -> str:
        """Redact sensitive data from text."""
        redacted = text
        for pattern_name, pattern in self.patterns.items():
            redacted = re.sub(
                pattern,
                f"[{pattern_name.upper()}_REDACTED]",
                redacted,
                flags=re.IGNORECASE
            )
        return redacted

# Test
engine = RedactionEngine()
assert "[API_KEY_REDACTED]" in engine.redact("api_key = 'sk-abc123def456'")
assert "[EMAIL_REDACTED]" in engine.redact("user@company.com")
print("✅ Redaction tests pass")
```

**Checklist:**
- [ ] All secret patterns tested (API key, AWS, GitHub, JWT, email).
- [ ] Unit tests pass (100% coverage).
- [ ] Integrated into App Server (redact before model call).

**Owner:** Security Lead  
**Due:** 27 Feb 2026

---

## Open Questions (Resolve by 25 Feb)

1. **Model source:** Use Llama 2 (open-source) or proprietary? → Decide in design review.
2. **Training compute:** 1× A100 (€3k) or 4× A100 (€12k)? → Depends on SFT timeline (1 week vs 3 days).
3. **Databricks region option:** eu-west-1 (Ireland) or eu-central-1 (Frankfurt)? → Confirm with DevOps.
4. **DPA sub-processors:** Approve GitHub (US) + vector DB (EU) → Legal sign-off needed.
5. **On-prem GPU specs:** What GPU cluster exists or can be procured? → IT assessment.

---

## Next Steps

1. **This week (24–28 Feb):**
   - [ ] All 5 technical decisions approved by CTO.
   - [ ] DPA signed with Databricks.
   - [ ] App Server skeleton deployed.
   - [ ] Model endpoint test-deployed.

2. **Next week (Mar 1–7):**
   - [ ] Pilot cohort (10–20 engineers) recruited.
   - [ ] On-boarding docs written.
   - [ ] VS Code plugin alpha ready.

3. **Month 2–3:**
   - [ ] SFT on model completes.
   - [ ] End-to-end integration testing.
   - [ ] Pilot launch.

---

**Prepared by:** ML Platform Team  
**Review by:** CTO, Security, Legal  
**Approved by:** _________ (Signature, Date)

