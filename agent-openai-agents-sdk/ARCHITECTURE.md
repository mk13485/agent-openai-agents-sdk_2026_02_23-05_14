# Copilot-Style Coding Agent Architecture

**Production-Ready Design Specification**
**Target: Slovakia Engineering Team | EU/GDPR Compliant**
**Date: February 23, 2026**

---

## 1. Executive Summary

This document defines a production architecture for an AI coding assistant comparable to GitHub Copilot / GPT-5.1 Codex. The system provides:

- **Contextual code completions** (single-line to full functions)
- **Agentic task orchestration** (multi-step refactoring, testing, verification loops)
- **Repository-aware suggestions** using code search and embeddings
- **Secure tool integration** (test runners, linters, CI/CD, PR creation)
- **EU/GDPR compliance** with data residency and privacy controls

### Design Priorities

1. **Accuracy**: High-quality, contextually relevant suggestions
2. **Safety**: Secure execution, secret redaction, license detection
3. **Low Latency**: <500ms for inline completions, <5s for agentic tasks
4. **Privacy**: EU data residency, opt-in/opt-out controls, minimal data transmission
5. **Extensibility**: Plugin architecture for tools, languages, and workflows
6. **Developer Ergonomics**: Seamless IDE integration, clear UX

---

## 2. System Architecture Overview

### 2.1 High-Level Components

```text
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ VS Code  │  │JetBrains │  │  Neovim  │  │  Web IDE │        │
│  │  Plugin  │  │  Plugin  │  │  Plugin  │  │          │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │              │             │               │
│       └─────────────┴──────────────┴─────────────┘               │
│                             │                                     │
└─────────────────────────────┼─────────────────────────────────────┘
                              │ HTTPS/WSS (TLS 1.3)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APP SERVER LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Gateway (Rate Limiting, Auth, Session Management)   │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│  ┌────────────┬───────────┴────────┬─────────────┬──────────┐   │
│  │  Context   │   Tool Proxy      │  Policy     │Telemetry │   │
│  │  Enricher  │   Orchestrator    │  Enforcer   │Ingestion │   │
│  └─────┬──────┴──────┬────────────┴──────┬──────┴────┬─────┘   │
└────────┼─────────────┼───────────────────┼───────────┼─────────┘
         │             │                   │           │
         ▼             ▼                   ▼           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFERENCE & EXECUTION LAYER                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  Model Serving   │  │ Execution Sandbox│  │ Repo Indexing│  │
│  │                  │  │                  │  │              │  │
│  │ • Fast Model     │  │ • Container Pool │  │ • Code Search│  │
│  │ • Agent Model    │  │ • Test Runners   │  │ • Embeddings │  │
│  │ • Tool Runtime   │  │ • Linters/Build  │  │ • Symbol DB  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA & OBSERVABILITY LAYER                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Training DB  │  │ Telemetry DB │  │  Monitoring/Logging  │  │
│  │              │  │              │  │                      │  │
│  │ • Labeled    │  │ • Usage Logs │  │ • Prometheus/Grafana│  │
│  │   Examples   │  │ • Acceptance │  │ • ELK Stack         │  │
│  │ • Feedback   │  │ • Errors     │  │ • Alerting          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow (Request Lifecycle)

1. **IDE Event** → User types code or issues task command
2. **Client Plugin** → Captures context (cursor position, open files, repo snapshot)
3. **App Server** →
   - Authenticates request
   - Enriches context (repo index, embeddings, code search results)
   - Enforces privacy policies (redact secrets, apply data minimization)
4. **Model Serving** →
   - Fast model generates inline completions OR
   - Agent model creates execution plan (multi-step tasks)
5. **Agent Runtime** (for agentic tasks) →
   - Executes plan steps in sandbox
   - Runs tests, linters, static analysis
   - Feeds results back to model for revision
   - Loops until pass/fail threshold
6. **App Server** → Returns results to client, logs telemetry
7. **Client Plugin** → Displays suggestions/diffs with confidence scores

---

## 3. Architecture Principles

### 3.1 Separation of Concerns

- **Client Layer**: UI/UX, local caching, privacy controls
- **App Server**: Protocol translation, session management, policy enforcement
- **Inference Layer**: Model serving, agent orchestration, execution isolation
- **Data Layer**: Persistence, indexing, observability

### 3.2 Security by Design

- Zero-trust architecture: every component authenticates/authorizes
- Secrets never leave client unless explicitly approved
- Sandboxed execution with network/filesystem restrictions
- Audit logs for all code changes and PR creations

### 3.3 Privacy by Default

- **Local-only mode**: All processing on device, no network calls
- **Partial mode**: Send only active file window (no repo context)
- **Full mode**: Send repo snapshot (opt-in, requires consent)
- EU data residency enforced at infrastructure level

### 3.4 Scalability & Performance

- Horizontal scaling for stateless components (API gateway, inference)
- Caching at multiple layers (IDE, app server, inference)
- Autoscaling based on load (GPU clusters, sandbox pools)
- Edge caching for frequent completions

---

## 4. Technology Stack Recommendations

### 4.1 Client (IDE Plugins)

- **VS Code**: TypeScript/JavaScript, Language Server Protocol
- **JetBrains**: Kotlin/Java, IntelliJ Platform SDK
- **Neovim**: Lua, LSP client
- **Web IDE**: TypeScript, Monaco Editor integration

### 4.2 App Server

- **Language**: Go or Rust (performance, concurrency)
- **Framework**: gRPC or GraphQL for API, WebSocket for streaming
- **Session Store**: Redis (distributed session state)
- **Message Queue**: RabbitMQ or Kafka (tool execution, async tasks)

### 4.3 Model Serving

- **Inference**: vLLM, TensorRT-LLM, or TGI (HuggingFace)
- **Hardware**: NVIDIA A100/H100 GPUs or TPU v5
- **Orchestration**: Kubernetes with GPU scheduling
- **Model Registry**: MLflow or Weights & Biases

### 4.4 Execution Sandbox

- **Container Runtime**: Docker or gVisor (enhanced isolation)
- **Orchestration**: Kubernetes Jobs or Nomad
- **Resource Limits**: CPU/memory quotas, network policies
- **Ephemeral Storage**: Tmpfs, auto-cleanup after task

### 4.5 Data Stores

- **Repo Index**: Elasticsearch or Meilisearch (code search)
- **Vector DB**: Qdrant, Weaviate, or pgvector (embeddings)
- **Relational**: PostgreSQL (user accounts, permissions, audit logs)
- **Time-series**: InfluxDB or Prometheus (metrics)

### 4.6 Observability

- **Metrics**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger or Tempo (distributed tracing)
- **Alerting**: PagerDuty or Opsgenie integration

---

## 5. EU/GDPR Compliance Architecture

### 5.1 Data Residency

- **Primary Hosting**: EU-based cloud (AWS eu-central-1/eu-west-1, Azure West Europe, GCP europe-west4)
- **Backup/DR**: Secondary EU region for disaster recovery
- **Data Transfer**: No cross-border transfers outside EU without explicit consent and adequacy mechanisms

### 5.2 Data Minimization

- **Default**: Send only necessary context (active file, cursor position)
- **Opt-in**: Repo-wide context requires user approval
- **Retention**: Telemetry anonymized after 30 days, training data after 90 days (or per policy)

### 5.3 User Rights

- **Access**: UI to view all data captured from user's sessions
- **Deletion**: One-click purge of all user data (telemetry, training samples)
- **Portability**: Export user data in JSON/CSV format
- **Objection**: Opt-out of training data usage with audit trail

### 5.4 Encryption

- **In-transit**: TLS 1.3 for all network communication
- **At-rest**: AES-256 encryption for databases and storage
- **Key Management**: Customer-managed keys (CMK) or BYOK option

---

## 6. Model Architecture

### 6.1 Two-Tier Model Strategy

#### Fast Completion Model (Tier 1)

- **Size**: 1-7B parameters
- **Latency**: <200ms (P95)
- **Use Case**: Inline completions, single-line suggestions
- **Deployment**: High-concurrency, autoscaling across many instances

#### Agent Model (Tier 2)

- **Size**: 20-70B parameters (or mixture-of-experts)
- **Latency**: 1-5s (acceptable for multi-step tasks)
- **Use Case**: Agentic workflows, multi-file refactoring, test generation
- **Deployment**: GPU-optimized, batch processing for efficiency

### 6.2 Tool-Use Integration

- **Function Calling**: Models trained with tool schemas (test runner, linter, git, CI)
- **Execution Loop**: Model outputs tool calls → sandbox executes → results fed back to model
- **Verification**: Model uses test results to refine code until pass criteria met

### 6.3 Context Management

- **Token Limits**: 8K-32K context window (depending on model family)
- **Context Prioritization**:
  1. Active file and cursor position
  2. Imported/referenced files
  3. Recently edited files
  4. Repo-wide search results (keyword-based)
  5. Embeddings for semantic similarity

---

## 7. Deployment Topologies

### 7.1 Option A: EU Cloud (Fastest to Deploy)

**Infrastructure**: AWS eu-central-1 (Frankfurt) or Azure West Europe (Netherlands)

```text
┌─────────────────────────────────────────────────────────────┐
│                    EU Cloud Region                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  VPC (Private Network)                              │    │
│  │  ┌───────────┐  ┌──────────┐  ┌─────────────────┐  │    │
│  │  │ App Server│  │  Model   │  │  Execution      │  │    │
│  │  │ (ECS/K8s) │  │ Serving  │  │  Sandbox (K8s)  │  │    │
│  │  │           │  │ (EKS/GPU)│  │                 │  │    │
│  │  └─────┬─────┘  └────┬─────┘  └────┬────────────┘  │    │
│  │        │             │             │               │    │
│  │  ┌─────┴─────────────┴─────────────┴────────────┐  │    │
│  │  │  RDS (PostgreSQL) + ElastiCache (Redis)      │  │    │
│  │  │  S3 (Encrypted) + OpenSearch (Code Index)    │  │    │
│  │  └───────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Pros**: Fast setup, managed services, autoscaling, high availability
**Cons**: Vendor lock-in, ongoing cloud costs, shared infrastructure

### 7.2 Option B: Hybrid (On-Prem Model + Cloud Control Plane)

**Infrastructure**: On-prem GPU cluster + EU cloud for app server and updates

```text
┌──────────────────────────┐       ┌─────────────────────────┐
│   On-Premises (Slovakia) │       │   EU Cloud (Control)    │
│  ┌────────────────────┐  │       │  ┌──────────────────┐   │
│  │  Model Serving     │  │◄─────►│  │  App Server      │   │
│  │  (Local GPUs)      │  │ VPN   │  │  (Session, Auth) │   │
│  │                    │  │       │  │                  │   │
│  │  Execution Sandbox │  │       │  │  Telemetry DB    │   │
│  │  (Local Compute)   │  │       │  │  Model Registry  │   │
│  └────────────────────┘  │       │  └──────────────────┘   │
└──────────────────────────┘       └─────────────────────────┘
```

**Pros**: Model code stays on-prem (sensitive repos), lower cloud costs
**Cons**: Hardware procurement, maintenance, slower scaling

### 7.3 Option C: Fully On-Prem (Maximum Security)

**Infrastructure**: All components in Slovakia datacenter or private cloud

```text
┌───────────────────────────────────────────────────────────┐
│         On-Premises Datacenter (Slovakia)                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │ App Server │  │   Model    │  │  Execution Sandbox │  │
│  │ (K8s)      │  │  Serving   │  │  (K8s)             │  │
│  │            │  │  (GPU Rack)│  │                    │  │
│  └─────┬──────┘  └─────┬──────┘  └──────┬─────────────┘  │
│        │               │                │                │
│  ┌─────┴───────────────┴────────────────┴─────────────┐  │
│  │  PostgreSQL + Redis + Elasticsearch + S3 (MinIO)   │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

**Pros**: Full control, maximum security, no vendor dependency
**Cons**: High capex, slower deployment, requires ops team

### 7.4 Recommended Approach for Slovakia Team

**Phase 1 (Months 0-3)**: EU Cloud (Option A) for rapid prototyping and pilot
**Phase 2 (Months 4-6)**: Evaluate Hybrid (Option B) if on-prem GPU investment justified
**Phase 3 (6+ months)**: Fully On-Prem (Option C) if regulatory or cost model demands

---

## 8. Scalability and Performance

### 8.1 Latency Targets

| Operation                     | Target (P95) | Target (P99) |
|-------------------------------|--------------|--------------|
| Inline completion (fast model)| <500ms       | <1s          |
| Multi-line completion         | <1s          | <2s          |
| Agentic task (single step)    | <5s          | <10s         |
| Full repo analysis            | <30s         | <60s         |

### 8.2 Throughput Targets

- **Completions**: 1,000 req/s per GPU node (batching enabled)
- **Agentic tasks**: 10-50 concurrent tasks per sandbox cluster
- **Users**: Support 100-1,000 developers in pilot phase

### 8.3 Scaling Strategies

1. **Horizontal Scaling**: Add more app server and inference nodes
2. **Caching**: Cache frequent completions (e.g., common imports, boilerplate)
3. **Request Prioritization**: Fast-track completions, queue agentic tasks
4. **Model Optimization**: Quantization (INT8/FP16), speculative decoding, KV-cache reuse

---

## 9. Observability and Monitoring

### 9.1 Key Metrics

| Metric                        | Description                                      | Alert Threshold |
|-------------------------------|--------------------------------------------------|-----------------|
| Completion Latency            | P95/P99 response time                            | >1s (P95)       |
| Acceptance Rate               | % of suggestions accepted by developers          | <30%            |
| Test Pass Rate                | % of generated code passing tests                | <70%            |
| Hallucination Rate            | % of suggestions with invalid API usage          | >10%            |
| Safety Incidents              | Count of security/license violations detected    | >0              |
| GPU Utilization               | % GPU compute in use                             | >90% sustained  |
| Sandbox Errors                | Failed test runs, timeouts                       | >5%             |

### 9.2 Dashboards

- **User Dashboard**: Acceptance rate, latency, top rejected suggestions
- **Ops Dashboard**: GPU utilization, sandbox health, error rates
- **ML Dashboard**: Model performance, drift detection, A/B test results

### 9.3 Alerting

- **Critical**: Service downtime, security incidents, data breaches
- **Warning**: High latency, low acceptance rate, model drift
- **Info**: Deployment completed, new model version available

---

## 10. Disaster Recovery and High Availability

### 10.1 Availability Targets

- **SLA**: 99.5% uptime (monthly, excludes planned maintenance)
- **RTO (Recovery Time Objective)**: <1 hour
- **RPO (Recovery Point Objective)**: <15 minutes

### 10.2 Redundancy

- **Multi-AZ Deployment**: Deploy across 3 availability zones in EU region
- **Database Replication**: PostgreSQL replica in secondary AZ, Redis Sentinel
- **Model Serving**: At least 2 inference nodes per model tier
- **Backup**: Daily snapshots, 30-day retention

### 10.3 Failover Strategy

1. **App Server**: Load balancer auto-routes to healthy nodes
2. **Model Serving**: Kubernetes liveness probes trigger pod restarts
3. **Database**: Automatic failover to replica (RDS Multi-AZ)
4. **Sandbox**: Isolated failures don't impact other components

---

## 11. Total Cost of Ownership (TCO) Estimate

### 11.1 Pilot Phase (10-20 Engineers, 3 Months)

| Component                 | Monthly Cost (EUR) | Notes                                |
|---------------------------|--------------------|--------------------------------------|
| GPU Compute (2x A100)     | €8,000             | On-demand or spot instances          |
| App Server (CPU)          | €1,000             | ECS/K8s cluster                      |
| Sandbox Compute           | €2,000             | Auto-scaling compute                 |
| Data Storage (DB, S3)     | €500               | 5TB storage + backups                |
| Networking (egress)       | €300               | Data transfer                        |
| Monitoring/Logging        | €200               | Prometheus, ELK                      |
| **Total**                 | **€12,000**        | Per month, full pilot infrastructure |

### 11.2 Production Phase (100-200 Engineers, 12 Months)

| Component                 | Monthly Cost (EUR) | Notes                                |
|---------------------------|--------------------|--------------------------------------|
| GPU Compute (10x A100)    | €40,000            | Reserved instances (discount)        |
| App Server (CPU)          | €5,000             | Multiple replicas                    |
| Sandbox Compute           | €10,000            | Higher concurrency                   |
| Data Storage (DB, S3)     | €2,000             | 50TB storage + backups               |
| Networking (egress)       | €1,500             | Increased traffic                    |
| Monitoring/Logging        | €1,000             | Advanced tooling                     |
| **Total**                 | **€59,500**        | Per month, production scale          |

**Annual Production TCO**: ~€715,000 (cloud-based)

**On-Prem Alternative**:

- **Capex**: €200,000-€500,000 (GPU servers, networking, storage)
- **Opex**: €10,000-€20,000/month (power, cooling, staff)
- **Break-even**: 12-18 months compared to cloud

---

## 12. Next Steps

1. **Technical Decision Workshop** (Week 1):
   - Finalize model family (open-source vs proprietary)
   - Choose deployment topology (cloud vs hybrid vs on-prem)
   - Define privacy policy and data retention rules

2. **Proof of Concept** (Weeks 2-4):
   - Build minimal app server and VS Code plugin
   - Integrate open-source code model (e.g., StarCoder, CodeLlama)
   - Test inline completions with 2-3 internal repos

3. **Architecture Review** (Week 5):
   - Security audit of PoC
   - Load testing and latency benchmarking
   - Cost validation against TCO estimates

4. **Pilot Launch** (Months 2-3):
   - Onboard 10-20 engineers across 2-3 teams
   - Collect telemetry and feedback
   - Iterate on UX and model quality

5. **Production Rollout** (Months 4-6):
   - Scale infrastructure for 100+ engineers
   - Implement RLHF training loop
   - Launch full feature set (agentic tasks, tool integrations)

---

## 13. References

- GitHub Copilot Documentation: [https://docs.github.com/copilot]
- OpenAI Codex Overview: [https://openai.com/blog/openai-codex]
- GDPR Guidelines for AI: [https://edpb.europa.eu]
- EU AI Act Compliance: [https://digital-strategy.ec.europa.eu]
- StarCoder (Open-Source Code Model): [https://huggingface.co/bigcode/starcoder]
- vLLM Inference Engine: [https://github.com/vllm-project/vllm]

---

**Document Version**: 1.0
**Last Updated**: February 23, 2026
**Owner**: Slovakia Engineering Team / AI Platform
**Review Cycle**: Quarterly
