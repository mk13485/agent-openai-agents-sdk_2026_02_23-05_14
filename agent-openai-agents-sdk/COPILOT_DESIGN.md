# Copilot-Style Coding Agent

## Production Implementation for Slovakia Engineering Team

**Design Date**: February 23, 2026
**Target**: EU/GDPR-compliant AI coding assistant
**Status**: Implementation-ready design

---

## 🎯 Executive Summary

This repository contains a complete, production-ready design for building a GitHub Copilot / GPT-5.1 Codex equivalent: an AI coding assistant that provides contextual code completions, multi-file refactoring, agentic task orchestration, and secure tool integration — all while meeting strict European data protection requirements.

### What's Included

✅ **Complete Architecture** - High-level system design with component diagrams
✅ **Detailed Component Specs** - Implementation-ready specifications for all services
✅ **Security & Privacy** - EU/GDPR compliance, secret detection, license attribution
✅ **Deployment Blueprint** - Infrastructure as Code, Kubernetes configs, CI/CD pipelines
✅ **6-Month Roadmap** - Week-by-week implementation plan with milestones
✅ **Training Plan** - Data collection, fine-tuning, RLHF, continuous learning
✅ **Budget & Resources** - Team structure, cost estimates, risk management

### Key Features

- **Inline Completions**: Single-line to full-function suggestions (<500ms P95 latency)
- **Agentic Workflows**: Multi-step tasks with test/run/verify loops
- **IDE Integration**: VS Code, JetBrains, Neovim plugins
- **EU Data Residency**: All data stored and processed in EU regions
- **Privacy Modes**: Local-only, partial, and full context modes
- **Secret Detection**: Client and server-side redaction of API keys, passwords
- **License Detection**: Warn users of potential copyright conflicts
- **Tool Execution**: Sandboxed test runners, linters, git operations
- **RLHF Training**: Continuous improvement from user feedback

---

## 📚 Documentation Structure

### Core Design Documents

| Document | Description | Read Time |
| -------- | ----------- | --------- |
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | System architecture, high-level design, component overview, data flow | 30 min |
| **[COMPONENTS.md](./COMPONENTS.md)** | Detailed specs for IDE plugins, App Server, Model Serving, Execution Sandbox, Data Stores, Monitoring | 90 min |
| **[SECURITY.md](./SECURITY.md)** | Privacy framework, GDPR compliance, secret detection, license checks, encryption, audit logging | 60 min |
| **[DEPLOYMENT.md](./DEPLOYMENT.md)** | Infrastructure as Code, Kubernetes configs, CI/CD pipelines, scaling strategies, disaster recovery | 75 min |
| **[ROADMAP.md](./ROADMAP.md)** | 6-month implementation plan, team structure, milestones, checklists, budget, success metrics | 45 min |
| **[TRAINING.md](./TRAINING.md)** | Data sources, training pipeline, fine-tuning, RLHF, evaluation, continuous learning | 60 min |

**Total Reading Time**: ~6 hours (recommended: read over 2-3 sessions)

### Quick Navigation

**Getting Started**:

1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system overview
2. Skim [ROADMAP.md](./ROADMAP.md) to understand timeline and phases
3. Review [DEPLOYMENT.md](./DEPLOYMENT.md) for infrastructure requirements

**For Engineers**:

- [COMPONENTS.md](./COMPONENTS.md) - Implementation details
- [TRAINING.md](./TRAINING.md) - ML pipeline and model training
- Code Examples - Sample implementations (below)

**For Product/Management**:

- [ROADMAP.md](./ROADMAP.md) - Timeline, budget, team structure
- Success Metrics - KPIs and evaluation criteria
- [SECURITY.md](./SECURITY.md) - Compliance and legal requirements

**For Security/Legal**:

- [SECURITY.md](./SECURITY.md) - GDPR, privacy, secrets management
- Data Governance - Ethical use and copyright

---

## 🚀 Quick Start (30 Minutes)

### Prerequisites

- **Cloud Account**: AWS, Azure, or GCP (EU regions)
- **Kubernetes**: EKS, AKS, or GKE cluster with GPU support
- **Tools**: `kubectl`, `helm`, `terraform`, `docker`
- **Access**: Container registry, domain for TLS

### Step 1: Clone and Setup

```bash
# Clone this repository
git clone https://github.com/your-org/copilot-agent
cd copilot-agent

# Set environment variables
export ENVIRONMENT=dev
export AWS_REGION=eu-central-1  # Or Azure/GCP equivalent
export CLUSTER_NAME=copilot-dev-cluster
```

### Step 2: Provision Infrastructure

```bash
# Navigate to Terraform directory
cd infra/terraform/environments/dev

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply (creates VPC, EKS, RDS, Redis, S3)
terraform apply -auto-approve

# Update kubeconfig
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION
```

**Expected Time**: 15-20 minutes

### Step 3: Deploy Services

```bash
# Install NVIDIA GPU Operator (for model serving)
helm install nvidia-gpu-operator \
  nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace

# Deploy Prometheus + Grafana (monitoring)
helm install prometheus-stack \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Deploy App Server
helm install app-server ./helm/charts/app-server \
  --namespace copilot-dev \
  --create-namespace \
  --values ./helm/values/dev.yaml

# Deploy Model Serving (with CodeLlama-7B)
helm install model-serving ./helm/charts/model-serving \
  --namespace copilot-dev \
  --values ./helm/values/dev.yaml \
  --set model.name=codellama/CodeLlama-7b-hf

# Check deployment status
kubectl get pods -n copilot-dev
```

**Expected Time**: 10-15 minutes

### Step 4: Install IDE Plugin (VS Code)

```bash
# Build VS Code extension
cd ide-plugins/vscode
npm install
npm run compile
npm run package  # Creates .vsix file

# Install in VS Code
code --install-extension copilot-agent-0.1.0.vsix

# Configure
# Open VS Code Settings, search for "Copilot Agent"
# Set API endpoint: https://api-dev.copilot.example.com
```

**Expected Time**: 5 minutes

### Step 5: Test End-to-End

1. Open a Python file in VS Code
2. Type: `def fibonacci(n):`
3. Wait for inline suggestion (ghost text)
4. Press `Tab` to accept suggestion
5. Check telemetry dashboard: <http://grafana.copilot-dev.svc.cluster.local>

✅ **If you see a completion, congratulations!** You have a working PoC.

---

## 🏗️ Architecture Overview

### High-Level System Design

```text
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ VS Code  │  │JetBrains │  │  Neovim  │  │  Web IDE │        │
│  │  Plugin  │  │  Plugin  │  │  Plugin  │  │          │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼──────────────┼─────────────┼──────────────┘
        │             │              │             │
        └─────────────┴──────────────┴─────────────┘
                            │ HTTPS/WSS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APP SERVER LAYER                            │
│  ┌────────────┐  ┌──────────────┐  ┌────────────┐  ┌─────────┐ │
│  │  Context   │  │ Tool Proxy   │  │  Policy    │  │Telemetry│ │
│  │  Enricher  │  │ Orchestrator │  │  Enforcer  │  │Ingestion│ │
│  └─────┬──────┘  └──────┬───────┘  └─────┬──────┘  └────┬────┘ │
└────────┼────────────────┼────────────────┼──────────────┼───────┘
         │                │                │              │
         ▼                ▼                ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 INFERENCE & EXECUTION LAYER                      │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │ Model Serving  │  │   Execution    │  │  Repo Indexing   │  │
│  │ (vLLM/TGI)     │  │   Sandbox      │  │ (Elasticsearch)  │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principles**:

- **Zero-Trust Security**: All components authenticate and authorize
- **Privacy by Default**: Minimal data transmission, EU data residency
- **Scalability**: Horizontal scaling for app server and model serving
- **Observability**: Metrics, logs, traces for all components

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed design.

---

## 💡 Key Design Decisions

### 1. Model Strategy: Open-Source First

**Decision**: Use CodeLlama-7B (fast model) + Mixtral-8x22B (agent model)

**Rationale**:

- ✅ Full control over model weights and training
- ✅ No data sent to third-party APIs (GDPR compliance)
- ✅ Lower cost (no per-token charges)
- ✅ Customizable for internal conventions

**Trade-off**: Requires ML expertise and GPU infrastructure

**Fallback**: Switch to GPT-4 API if quality insufficient (with EU data residency option)

### 2. Hosting: EU Cloud (AWS eu-central-1)

**Decision**: Start with AWS Frankfurt region, fully managed services

**Rationale**:

- ✅ Fast deployment (EKS, RDS, S3 readily available)
- ✅ Data residency guaranteed (no cross-border transfers)
- ✅ High availability with Multi-AZ
- ✅ Cost-effective for pilot phase

**Alternative**: Hybrid (on-prem GPU + cloud control plane) for production if cost/security demands

### 3. IDE Priority: VS Code First, Then JetBrains and Neovim

**Decision**: Build VS Code plugin in Month 2, JetBrains in Month 5

**Rationale**:

- 60%+ of developers use VS Code (largest user base)
- TypeScript ecosystem mature for extensions
- Fastest time to pilot

**Trade-off**: JetBrains users wait longer

### 4. Privacy: Three-Tier Model (Local, Partial, Full)

**Decision**: Default to Partial mode (active file only), opt-in for Full mode

**Rationale**:

- ✅ Balances privacy and functionality
- ✅ GDPR-compliant (minimal data by default)
- ✅ Gives users control (transparency)

**Implementation**: See [SECURITY.md](./SECURITY.md)

### 5. Training: RLHF from Day 1

**Decision**: Implement RLHF loop in Month 5 (not after launch)

**Rationale**:

- Continuous improvement baked into architecture
- Faster iteration based on real user feedback
- Competitive advantage (model improves over time)

**Trade-off**: Additional complexity and compute cost

---

## 📊 Success Metrics

### Primary OKRs (6 Months)

#### Objective 1: High-Quality Suggestions

- ✅ **Acceptance Rate >60%** (% of suggestions accepted by users)
- ✅ **Test Pass Rate >70%** (% of generated code passing tests)
- ✅ **Hallucination Rate <10%** (% of invalid API usage)

#### Objective 2: Reliability & Performance

- ✅ **Uptime 99.5%** (SLA)
- ✅ **Latency <500ms** (P95 for inline completions)
- ✅ **Zero Critical Security Incidents**

#### Objective 3: User Satisfaction

- ✅ **NPS >50** (Net Promoter Score)
- ✅ **80% Weekly Active** (users with >10 completions/week)
- ✅ **70% Positive Feedback** from pilot users

#### Objective 4: GDPR Compliance

- ✅ **100% EU Data Residency** (verified)
- ✅ **All User Rights Implemented** (access, delete, export)
- ✅ **PIA Approved** (Privacy Impact Assessment)

### Secondary Metrics

- Daily Active Users (DAU)
- Completions per user per day
- Cost per user (<€50/month target)
- GPU utilization (target: 70-80%)
- Cache hit rate (target: >30%)

See [ROADMAP.md](./ROADMAP.md) for detailed success criteria.

---

## 💰 Budget Summary

### 6-Month Total: ~€435,000

| Category | Amount (EUR) | Notes |
| -------- | ------------ | ----- |
| **Infrastructure** | €100,000 | AWS/Azure (GPU, CPU, storage, network) |
| **Team Salaries** | €307,500 | 8-12 people for 6 months |
| **Security Audit** | €15,000 | Third-party penetration testing |
| **Legal/GDPR** | €5,000 | Consultation and compliance |
| **Tools & Licenses** | €3,000 | IDEs, Jira, monitoring tools |
| **Training/Conferences** | €5,000 | Team learning (optional) |

**Monthly Average**: ~€72,500

**Cost Per User (Production)**: €25-€35/month (for 100-200 users)

**Break-Even vs Commercial API** (e.g., GitHub Copilot at $10/user/month): 12-18 months

See [ROADMAP.md](./ROADMAP.md) for detailed breakdown.

---

## 👥 Team Structure

### Recommended: 8-12 People

**Engineering (7)**:

- 1x Tech Lead / Architect
- 2x Backend Engineers (App Server, API)
- 2x ML Engineers (Model training, inference)
- 2x Frontend/IDE Engineers (VS Code, JetBrains, Neovim)

**Operations (2)**:

- 1-2x DevOps/SRE (Infrastructure, CI/CD, monitoring)

**Product & Design (2)**:

- 1x Product Manager
- 0.5-1x UX Designer

**Security (0.5)**:

- Part-time Security Consultant or Engineer

See [ROADMAP.md](./ROADMAP.md) for roles and responsibilities.

---

## 🗓️ 6-Month Timeline

### Month 1-2: Foundation & PoC

- Team assembly, infrastructure setup
- App Server skeleton, model serving PoC
- VS Code plugin prototype
- **Milestone**: First end-to-end completion

### Month 3-4: Pilot Launch

- Agent runtime, execution sandbox
- Chat pane, privacy controls
- License detection, security audit
- **Milestone**: 10-20 users in pilot

### Month 5-6: Production Rollout

- Scale infrastructure (multi-AZ, autoscaling)
- JetBrains and Neovim plugins
- RLHF training loop
- **Milestone**: 100-200+ users, 99.5% uptime

See [ROADMAP.md](./ROADMAP.md) for week-by-week details.

---

## 🔒 Security & Compliance

### GDPR Compliance

✅ **Data Residency**: All data in EU (AWS eu-central-1, Azure West Europe, or GCP europe-west4)
✅ **User Consent**: Explicit opt-in for Full mode and training data usage
✅ **User Rights**: Access, deletion, portability, objection
✅ **Data Minimization**: Partial mode by default (active file only)
✅ **Retention**: 30 days telemetry, 90 days training data, 3 years audit logs
✅ **Encryption**: TLS 1.3 (transit), AES-256 (rest)
✅ **Audit Logging**: Immutable logs, 3-year retention

### Security Features

✅ **Secret Detection**: Client and server-side redaction of API keys, passwords, tokens
✅ **License Detection**: Warn users of potential copyright conflicts (GPL, proprietary)
✅ **Sandbox Isolation**: Container-based execution with no network access
✅ **Zero-Trust Architecture**: All components authenticate and authorize
✅ **Vulnerability Scanning**: Trivy, govulncheck in CI/CD pipeline
✅ **Penetration Testing**: Third-party audit scheduled (Month 4)

See [SECURITY.md](./SECURITY.md) for comprehensive security controls.

---

## 📖 Code Examples

### Example 1: Inline Completion Request (VS Code Plugin)

```typescript
// ide-plugins/vscode/src/completion-provider.ts
import * as vscode from 'vscode';
import { ApiClient } from './api-client';

export class CopilotCompletionProvider implements vscode.InlineCompletionItemProvider {
    private apiClient: ApiClient;

    constructor(apiClient: ApiClient) {
        this.apiClient = apiClient;
    }

    async provideInlineCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        context: vscode.InlineCompletionContext,
        token: vscode.CancellationToken
    ): Promise<vscode.InlineCompletionItem[]> {
        // Get text before and after cursor
        const textBeforeCursor = document.getText(
            new vscode.Range(new vscode.Position(0, 0), position)
        );
        const textAfterCursor = document.getText(
            new vscode.Range(position, document.lineAt(document.lineCount - 1).range.end)
        );

        // Request completion from API
        const response = await this.apiClient.requestCompletion({
            filePath: document.fileName,
            language: document.languageId,
            cursorPosition: { line: position.line, character: position.character },
            textBeforeCursor: textBeforeCursor.slice(-2000), // Last 2000 chars
            textAfterCursor: textAfterCursor.slice(0, 500),  // Next 500 chars
            privacyMode: vscode.workspace.getConfiguration('copilot').get('privacyMode', 'partial')
        });

        // Convert to VS Code inline completion items
        return response.suggestions.map(suggestion => {
            const item = new vscode.InlineCompletionItem(suggestion.text);
            item.range = new vscode.Range(position, position.translate(0, suggestion.text.length));
            return item;
        });
    }
}
```

### Example 2: App Server Context Enrichment

```go
// app-server/context/enricher.go
package context

import (
    "fmt"
    "github.com/elastic/go-elasticsearch/v8"
)

type ContextEnricher struct {
    esClient *elasticsearch.Client
    vectorDB *VectorDBClient
}

func (e *ContextEnricher) EnrichContext(req *CompletionRequest) (*ModelContext, error) {
    ctx := &ModelContext{}

    // Priority 1: Active file
    ctx.AddText(req.TextBeforeCursor, 10)
    ctx.AddText(req.TextAfterCursor, 9)

    // Priority 2: Imported files
    imports := extractImports(req.TextBeforeCursor, req.Language)
    for _, imp := range imports {
        fileContent, err := e.fetchFileFromIndex(req.RepoID, imp)
        if err == nil {
            ctx.AddFile(fileContent, 8)
        }
    }

    // Priority 3: Semantic search (if Full mode)
    if req.PrivacyMode == "full" {
        embeddings, err := e.vectorDB.Search(req.TextBeforeCursor, 3)
        if err == nil {
            for _, emb := range embeddings {
                ctx.AddSnippet(emb.Text, 6)
            }
        }
    }

    // Truncate to model's context window
    return ctx.TruncateToTokens(8000), nil
}

func (e *ContextEnricher) fetchFileFromIndex(repoID, filePath string) (string, error) {
    res, err := e.esClient.Search(
        e.esClient.Search.WithBody(map[string]interface{}{
            "query": map[string]interface{}{
                "bool": map[string]interface{}{
                    "must": []map[string]interface{}{
                        {"term": map[string]string{"repoId": repoID}},
                        {"term": map[string]string{"filePath": filePath}},
                    },
                },
            },
        }),
    )
    if err != nil {
        return "", err
    }
    // Parse response and return file content
    // ... (parsing logic omitted)
    return "", nil
}
```

### Example 3: Agent Runtime (Execution Loop)

```python
# app-server/agent/runtime.py
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class AgentRuntime:
    def __init__(self, model_client, tool_proxy, max_iterations=5):
        self.model_client = model_client
        self.tool_proxy = tool_proxy
        self.max_iterations = max_iterations

    async def run_task(self, user_request: str, context: dict) -> Dict:
        """Execute agentic task with tool use and verification."""
        conversation = [
            {"role": "system", "content": "You are a coding assistant with tools."},
            {"role": "user", "content": user_request}
        ]

        for iteration in range(self.max_iterations):
            logger.info(f"Agent iteration {iteration + 1}/{self.max_iterations}")

            # Get model response
            response = await self.model_client.chat_completion(
                messages=conversation,
                tools=self.tool_proxy.get_tool_schemas(),
                context=context
            )

            conversation.append({"role": "assistant", "content": response.get("content"), "tool_calls": response.get("tool_calls")})

            # Parse tool calls
            tool_calls = response.get("tool_calls", [])

            if not tool_calls:
                # No more tools, agent is done
                logger.info("Agent completed task (no more tool calls)")
                return {"success": True, "output": response["content"], "iterations": iteration + 1}

            # Execute tools
            tool_results = []
            all_passed = True
            for tool_call in tool_calls:
                result = await self.tool_proxy.execute_tool(
                    name=tool_call["function"]["name"],
                    args=tool_call["function"]["arguments"]
                )
                tool_results.append(result)

                if result.status != "pass":
                    all_passed = False

                conversation.append({
                    "role": "tool",
                    "content": result.to_json(),
                    "tool_call_id": tool_call["id"]
                })

            # Check verification
            if all_passed:
                logger.info("All tools passed, task complete")
                return {"success": True, "output": response["content"], "tool_results": tool_results, "iterations": iteration + 1}

        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached without completion")
        return {"success": False, "error": "Max iterations exceeded", "iterations": self.max_iterations}
```

---

## 🤝 Contributing

This is an implementation design. To contribute:

1. **Feedback**: Open issues for questions, suggestions, or improvements
2. **Implementations**: Share your implementation experiences, code snippets, or lessons learned
3. **Extensions**: Propose additional features or alternative approaches

### Guidelines

- **Respect GDPR**: Any contributions must maintain EU data protection compliance
- **Security First**: Follow security best practices (no hardcoded secrets, input validation, etc.)
- **Document**: Add comments and documentation for complex logic

---

## 📄 License

This design document is provided under **CC BY 4.0** (Creative Commons Attribution 4.0 International).

You are free to:

- **Share**: Copy and redistribute in any medium or format
- **Adapt**: Remix, transform, and build upon the material

Under the following terms:

- **Attribution**: Give appropriate credit, provide a link to the license, and indicate if changes were made

**Code examples** (if any) are provided under **MIT License**.

---

## 🆘 Support & Contact

### Questions?

- **Technical**: Open an issue with `[Question]` tag
- **Security**: Email <security@copilot-team.example.com> (PGP key available)
- **Legal/GDPR**: Email <legal@copilot-team.example.com>

### Resources

- **Slack**: #copilot-agent (internal team channel)
- **Documentation**: <https://docs.copilot-agent.example.com> (once deployed)
- **Status Page**: <https://status.copilot-agent.example.com> (uptime, incidents)

### Team

**Designed by**: Slovakia Engineering Team
**Contact**: <tech-lead@copilot-team.example.com>

---

## 🎉 Acknowledgments

This design draws inspiration and best practices from:

- **GitHub Copilot**: Product features and UX patterns
- **OpenAI Codex**: Model architecture and capabilities
- **Agentic Engineering**: Self-correcting development environments
- **HuggingFace BigCode**: The Stack dataset and StarCoder model
- **EU GDPR**: Data protection by design principles

Special thanks to the open-source community for tools like vLLM, Kubernetes, Terraform, and countless libraries that make this possible.

---

## 📅 Document History

| Version | Date         | Changes                 |
| ------- | ------------ | ----------------------- |
| 1.0     | Feb 23, 2026 | Initial complete design |

---

**Ready to build?** Start with [ROADMAP.md](./ROADMAP.md) for your first week's tasks. 🚀
