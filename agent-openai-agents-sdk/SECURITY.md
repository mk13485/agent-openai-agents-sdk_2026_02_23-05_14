# Security & Privacy Controls
**Copilot-Style Coding Agent - EU/GDPR Compliance**
**Date: February 23, 2026**

---

## Table of Contents

1. [Privacy Framework](#1-privacy-framework)
2. [EU/GDPR Compliance](#2-eugdpr-compliance)
3. [Security Architecture](#3-security-architecture)
4. [Secret Detection & Redaction](#4-secret-detection--redaction)
5. [License Detection & Attribution](#5-license-detection--attribution)
6. [Access Control & Authentication](#6-access-control--authentication)
7. [Data Encryption](#7-data-encryption)
8. [Audit Logging](#8-audit-logging)
9. [Incident Response](#9-incident-response)
10. [Compliance Checklist](#10-compliance-checklist)

---

## 1. Privacy Framework

### 1.1 Privacy by Design Principles

1. **Data Minimization**: Collect only the minimum data needed for functionality
2. **Purpose Limitation**: Use data only for stated purposes (code assistance)
3. **Storage Limitation**: Retain data only as long as necessary
4. **Transparency**: Clear communication about what data is collected and why
5. **User Control**: Give users control over their data (view, delete, export)

### 1.2 Privacy Modes

Users can select their preferred privacy level in IDE settings:

#### Local-Only Mode
- **Description**: All processing happens on user's machine, no data sent to server
- **Features Available**: Basic completions using local model (if hardware permits)
- **Features Unavailable**: Repo-wide context, agentic tasks, model improvements
- **Use Case**: Highly sensitive codebases, legal/compliance requirements

#### Partial Mode (Default)
- **Description**: Send only active file window and cursor position
- **Data Transmitted**:
  - Current file name and language
  - 2000 characters before cursor
  - 500 characters after cursor
  - List of imports in current file
- **Not Transmitted**: Full repo, other files, git history, environment variables
- **Use Case**: Balance between privacy and functionality

#### Full Mode (Opt-In)
- **Description**: Send full repo context for best suggestions
- **Data Transmitted**:
  - All data from Partial mode
  - Full repository snapshot (up to 100 MB)
  - Recently edited files
  - Git commit messages (last 50)
  - Project dependencies (requirements.txt, package.json, etc.)
- **Consent Required**: Explicit opt-in per repository
- **Use Case**: Maximum code assistance quality, team collaboration

### 1.3 Privacy Dashboard

Users can access a privacy dashboard to view and manage their data:

```
┌─────────────────────────────────────────────────────────┐
│  Your Privacy Dashboard                                 │
│                                                          │
│  Current Mode: Partial                                  │
│  Data Collected This Week: 42.3 MB                      │
│  Requests Made: 1,247                                   │
│                                                          │
│  Repositories (3):                                      │
│  ✓ company/web-app (Full mode, expires in 89 days)     │
│  ✓ company/api-server (Partial mode)                   │
│  ✓ personal/side-project (Local-only mode)             │
│                                                          │
│  Training Data:                                         │
│  ☐ Allow my accepted suggestions for model training    │
│    (Helps improve model for everyone)                   │
│                                                          │
│  Actions:                                               │
│  [View Collected Data] [Export Data] [Delete All Data]  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. EU/GDPR Compliance

### 2.1 Data Residency

**Requirement**: All personal data of EU users must be stored and processed within the EU.

**Implementation**:
- **Primary Region**: AWS eu-central-1 (Frankfurt) or Azure West Europe (Netherlands)
- **Backup Region**: AWS eu-west-1 (Ireland) or Azure North Europe (Finland)
- **No Cross-Border Transfers**: Zero data transfers to US or other non-EU regions
- **Cloud Provider Commitments**: Use providers with GDPR-compliant data processing agreements (DPAs)

**Infrastructure Tagging**:
```yaml
# Terraform/CloudFormation
Tags:
  DataResidency: "EU"
  GDPRCompliant: "true"
  Purpose: "CodingAssistant"
```

**Verification**:
- Quarterly audits of data locations
- Automated checks for accidental cross-region replication
- Alert if any service attempts to route data outside EU

### 2.2 Legal Basis for Processing

Under GDPR Article 6, we process data based on:

1. **Consent** (Article 6(1)(a)): User explicitly opts in to Full mode
2. **Contractual Necessity** (Article 6(1)(b)): Processing required to provide service
3. **Legitimate Interest** (Article 6(1)(f)): Improve service, prevent fraud (balanced against user rights)

**Consent Management**:
```typescript
interface ConsentRecord {
  userId: string;
  consentType: 'partial_mode' | 'full_mode' | 'training_data';
  granted: boolean;
  timestamp: string;
  expiresAt?: string;  // Re-consent after 1 year
  withdrawnAt?: string;
}
```

### 2.3 User Rights Implementation

#### Right of Access (Article 15)
Users can request all data held about them.

**Implementation**:
```bash
# API endpoint
GET /api/v1/gdpr/data-access?userId={userId}

# Response includes:
{
  "sessions": [...],           # All sessions
  "completions": [...],        # Sent/received completions
  "telemetry": [...],          # Usage metrics
  "training_samples": [...]    # If opted into training
}
```

#### Right to Erasure (Article 17)
Users can delete all their data.

**Implementation**:
```sql
-- Delete from all tables
DELETE FROM sessions WHERE user_id = $1;
DELETE FROM telemetry_events WHERE user_id = $1;
DELETE FROM audit_logs WHERE user_id = $1;
DELETE FROM training_data WHERE user_id = $1;

-- Cascade to related records
-- Also trigger deletion from:
-- - Redis session cache
-- - Elasticsearch logs (manual purge)
-- - S3 training data files
```

**Timeline**: Complete deletion within 30 days (GDPR requirement)

#### Right to Data Portability (Article 20)
Users can export data in machine-readable format.

**Implementation**:
```bash
# Export as JSON
GET /api/v1/gdpr/data-export?userId={userId}&format=json

# Export as CSV
GET /api/v1/gdpr/data-export?userId={userId}&format=csv
```

#### Right to Object (Article 21)
Users can opt out of training data usage, even if previously consented.

**Implementation**:
- Toggle in privacy dashboard
- Immediately stop using their data for training
- Option to delete previously collected training samples

### 2.4 Data Retention Policy

| Data Type              | Retention Period | Basis                          |
|------------------------|------------------|--------------------------------|
| Active sessions        | 1 hour           | Session timeout                |
| Telemetry (raw)        | 30 days          | Operational debugging          |
| Telemetry (aggregated) | 2 years          | Product analytics              |
| Audit logs             | 3 years          | Compliance, security           |
| Training data          | 90 days          | Model improvement (if opted in)|
| User account           | Until deletion   | Contractual necessity          |

**Automated Cleanup**:
```python
# Cron job runs daily
def cleanup_expired_data():
    # Delete old sessions
    db.execute("DELETE FROM sessions WHERE last_activity < NOW() - INTERVAL '1 hour'")

    # Delete old telemetry
    db.execute("DELETE FROM telemetry_events WHERE timestamp < NOW() - INTERVAL '30 days'")

    # Delete expired training data
    s3.delete_objects_older_than("training-data/", days=90)
```

### 2.5 Data Processing Agreement (DPA)

**Required Elements** (for enterprise customers):
- Detailed description of processing activities
- Types of personal data processed
- Categories of data subjects (developers, admins)
- Security measures implemented
- Sub-processor list (cloud providers, monitoring tools)
- Data breach notification procedures

**Template**: See `docs/DPA_template.pdf`

### 2.6 Privacy Impact Assessment (PIA)

**Conducted**: February 2026
**Next Review**: August 2026 (every 6 months)

**Key Findings**:
- **High Risk**: Processing of intellectual property (code) → Mitigated by privacy modes and encryption
- **Medium Risk**: Training on user data → Mitigated by explicit opt-in and anonymization
- **Low Risk**: Telemetry collection → Mitigated by aggregation and short retention

**Actions**:
- ✓ Implement three-tier privacy modes
- ✓ Deploy EU-only infrastructure
- ✓ Add user data export/deletion features
- [ ] Regular third-party security audits (Q3 2026)

---

## 3. Security Architecture

### 3.1 Zero-Trust Principles

1. **Never Trust, Always Verify**: All requests authenticated and authorized
2. **Least Privilege**: Services and users have minimal necessary permissions
3. **Assume Breach**: Design for containment and rapid detection
4. **Encrypt Everything**: Data in transit and at rest

### 3.2 Network Segmentation

```
┌─────────────────────────────────────────────────────────┐
│  PUBLIC INTERNET                                        │
└─────────────────┬───────────────────────────────────────┘
                  │
         ┌────────▼────────┐
         │  WAF + DDoS     │
         │  Protection     │
         └────────┬────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│  DMZ (Public Subnet)                                    │
│  ┌──────────────────┐                                   │
│  │  Load Balancer   │                                   │
│  │  (TLS Termination│                                   │
│  └────────┬─────────┘                                   │
└───────────┼─────────────────────────────────────────────┘
            │
┌───────────▼─────────────────────────────────────────────┐
│  APPLICATION SUBNET (Private)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │ App Server  │  │   Model     │  │  Sandbox       │  │
│  │             │  │   Serving   │  │  (Isolated)    │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────────┘  │
└─────────┼────────────────┼─────────────────────────────┘
          │                │
┌─────────▼────────────────▼─────────────────────────────┐
│  DATA SUBNET (Private, No Internet)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │ PostgreSQL  │  │ Redis       │  │ Elasticsearch  │  │
│  │             │  │             │  │                │  │
│  └─────────────┘  └─────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Firewall Rules**:
- Internet → WAF: HTTPS (443)
- WAF → Load Balancer: HTTPS (443)
- Load Balancer → App Server: HTTP (8080), internal network only
- App Server → Model Serving: gRPC (50051), internal network only
- Sandbox: **No outbound network** (network isolation)
- App Server → Databases: PostgreSQL (5432), Redis (6379), internal network only
- Databases: **No internet access**

### 3.3 Container Security

#### Sandbox Hardening
```dockerfile
FROM python:3.11-slim AS base

# Security: Remove unnecessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Security: Create non-root user
RUN useradd -m -u 1000 -s /bin/false sandbox

# Security: Set secure permissions
RUN chmod 700 /home/sandbox

# Switch to non-root user
USER sandbox
WORKDIR /workspace

# Security: Drop capabilities (Kubernetes)
# securityContext:
#   runAsNonRoot: true
#   runAsUser: 1000
#   capabilities:
#     drop: ["ALL"]
#   readOnlyRootFilesystem: true
```

#### Seccomp Profile (Restrict Syscalls)
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat", "lseek", "mmap", "brk", "exit_group"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

**Blocked Syscalls**: `mount`, `reboot`, `syslog`, `ptrace`, `setuid`, `setgid`, `chroot`

### 3.4 Secrets Management

**Never Hardcode Secrets**: All secrets stored in secret management system.

**Options**:
1. **AWS Secrets Manager** (for AWS deployments)
2. **Azure Key Vault** (for Azure deployments)
3. **HashiCorp Vault** (cloud-agnostic)
4. **Kubernetes Secrets** + **Sealed Secrets** (for K8s)

**Example** (Kubernetes with External Secrets Operator):
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-server-secrets
spec:
  refreshInterval: 15m
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: app-server-secrets
  data:
  - secretKey: postgres-password
    remoteRef:
      key: /copilot/prod/postgres-password
  - secretKey: redis-password
    remoteRef:
      key: /copilot/prod/redis-password
  - secretKey: model-api-key
    remoteRef:
      key: /copilot/prod/model-api-key
```

**Secret Rotation**:
- **Database passwords**: Rotate every 90 days (automated)
- **API keys**: Rotate every 180 days or on suspected compromise
- **JWT signing keys**: Rotate every 90 days, maintain 2 active keys (old + new) during transition

### 3.5 Vulnerability Management

**Container Scanning**:
```bash
# Scan images for vulnerabilities (Trivy)
trivy image --severity HIGH,CRITICAL app-server:v1.0.0

# Block deployment if critical vulnerabilities found
if trivy image ... | grep CRITICAL; then
  echo "Critical vulnerabilities found, blocking deployment"
  exit 1
fi
```

**Dependency Scanning**:
```bash
# Python (pip-audit)
pip-audit --desc

# Node.js (npm audit)
npm audit --audit-level=high

# Go (govulncheck)
govulncheck ./...
```

**Automated Updates**:
- Dependabot (GitHub): Auto-create PRs for dependency updates
- Renovate Bot: More configurable alternative
- Weekly review and merge of security patches

### 3.6 DDoS Protection

**Layers**:
1. **Cloud Provider**: AWS Shield, Cloudflare
2. **Rate Limiting**: Per-IP, per-user, per-org limits
3. **WAF Rules**: Block malicious patterns, known bad IPs
4. **Admission Control**: Reject requests when system overloaded

**Rate Limits** (implemented in API Gateway):
```go
// Per-IP rate limit (anonymous users)
rateLimitPerIP := 100  // requests per minute

// Per-user rate limit
rateLimitPerUser := 1000  // requests per hour

// Per-org rate limit
rateLimitPerOrg := 10000  // requests per hour
```

---

## 4. Secret Detection & Redaction

### 4.1 Overview

Secrets (API keys, passwords, tokens) must never be sent to the model or stored in logs/training data.

### 4.2 Detection Patterns

**Regex Patterns**:
```python
SECRET_PATTERNS = {
    'api_key': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
    'password': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']+)["\']',
    'openai_key': r'sk-[a-zA-Z0-9]{48}',
    'github_token': r'ghp_[a-zA-Z0-9]{36}',
    'aws_key': r'AKIA[0-9A-Z]{16}',
    'private_key': r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----',
    'jwt': r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
    'connection_string': r'(?i)(mongodb|postgres|mysql):\/\/[^:]+:[^@]+@[\w.:-]+',
}
```

**Machine Learning Detection**:
- Train classifier on labeled secrets dataset
- Detects non-standard secret formats
- Higher accuracy but more compute-intensive

**Combined Approach**:
1. Fast regex scan (CPU-cheap, 95% recall)
2. ML classifier for flagged lines (high precision)

### 4.3 Redaction Process

**Client-Side** (IDE Plugin):
```typescript
function redactSecrets(code: string): {redacted: string, detected: string[]} {
  let redacted = code;
  const detected: string[] = [];

  for (const [name, pattern] of Object.entries(SECRET_PATTERNS)) {
    const matches = code.matchAll(new RegExp(pattern, 'g'));
    for (const match of matches) {
      redacted = redacted.replace(match[0], `<REDACTED_${name.toUpperCase()}>`);
      detected.push(name);
    }
  }

  return {redacted, detected};
}

// Before sending to server
const {redacted, detected} = redactSecrets(codeContext);
if (detected.length > 0) {
  showNotification(`Secrets detected and redacted: ${detected.join(', ')}`);
}
sendToServer(redacted);
```

**Server-Side** (Double-Check):
```python
def redact_secrets_server(code: str) -> tuple[str, list[str]]:
    """Server-side redaction as failsafe."""
    redacted = code
    detected = []

    for name, pattern in SECRET_PATTERNS.items():
        matches = re.findall(pattern, code, re.IGNORECASE)
        if matches:
            for match in matches:
                secret_value = match[1] if isinstance(match, tuple) else match
                redacted = redacted.replace(secret_value, f'<REDACTED_{name.upper()}>')
                detected.append(name)

                # ALERT: Secret reached server (should have been caught client-side)
                logger.warning(f"Secret {name} detected on server for user {user_id}")
                metrics.increment('secrets_detected_server', tags=[f'type:{name}'])

    return redacted, detected
```

### 4.4 User Notification

**Visual Indicator** (IDE):
```
┌────────────────────────────────────────────────┐
│  ⚠️  Secret Detected                          │
│                                                │
│  We detected an API key in your code.         │
│  It was NOT sent to the server.               │
│                                                │
│  File: src/config.py                           │
│  Line: 15                                      │
│  Type: API Key                                 │
│                                                │
│  [View Line] [Ignore] [Learn More]            │
└────────────────────────────────────────────────┘
```

### 4.5 Training Data Filtering

Before using accepted suggestions for training:
```python
def is_safe_for_training(completion: str) -> bool:
    # Check for secrets
    _, detected = redact_secrets_server(completion)
    if detected:
        logger.info(f"Rejected training sample: contains secrets")
        return False

    # Check for PII (emails, phone numbers, names in comments)
    if contains_pii(completion):
        logger.info(f"Rejected training sample: contains PII")
        return False

    # Check for offensive content
    if contains_offensive_content(completion):
        logger.info(f"Rejected training sample: offensive content")
        return False

    return True
```

---

## 5. License Detection & Attribution

### 5.1 Overview

Suggested code may unintentionally match copyrighted code. Detect and notify users.

### 5.2 Detection Methods

#### Exact Match (Fast)
- Hash suggested code (e.g., SHA-256)
- Check against database of known code snippets with licenses
- Database built from public code corpora (GitHub, GitLab, Bitbucket)

```python
import hashlib

def check_exact_match(code: str) -> Optional[Match]:
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    # Query license database
    match = license_db.query(code_hash)

    if match:
        return Match(
            license=match.license,
            repo=match.repo_url,
            confidence=1.0  # Exact match
        )
    return None
```

#### Fuzzy Match (Slower, More Accurate)
- Use Locality-Sensitive Hashing (LSH) or MinHash
- Detect similar (not just identical) code
- Higher recall, lower precision

```python
from datasketch import MinHash, MinHashLSH

def build_lsh_index(code_corpus: list[CodeSnippet]):
    lsh = MinHashLSH(threshold=0.8, num_perm=128)

    for snippet in code_corpus:
        minhash = MinHash(num_perm=128)
        for token in tokenize(snippet.code):
            minhash.update(token.encode())
        lsh.insert(snippet.id, minhash)

    return lsh

def check_fuzzy_match(code: str, lsh: MinHashLSH) -> list[Match]:
    minhash = MinHash(num_perm=128)
    for token in tokenize(code):
        minhash.update(token.encode())

    similar_ids = lsh.query(minhash)

    matches = []
    for snippet_id in similar_ids:
        snippet = license_db.get_snippet(snippet_id)
        similarity = compute_similarity(code, snippet.code)

        if similarity > 0.8:
            matches.append(Match(
                license=snippet.license,
                repo=snippet.repo_url,
                confidence=similarity
            ))

    return matches
```

### 5.3 User Notification

**Low Confidence Match** (0.6-0.8 similarity):
```
ℹ️  This suggestion may be similar to existing code.
   License: MIT | Source: github.com/example/repo
   [View Source] [Dismiss]
```

**High Confidence Match** (>0.8 similarity):
```
⚠️  Warning: This code closely matches existing copyrighted code.
   License: GPL-3.0 (Viral License)
   Source: github.com/example/gpl-project

   Using this code may require you to open-source your project.

   [View Source] [Generate Alternative] [Use Anyway]
```

### 5.4 License Database

**Schema**:
```sql
CREATE TABLE license_matches (
    id BIGSERIAL PRIMARY KEY,
    code_hash VARCHAR(64) UNIQUE,  -- SHA-256
    minhash BYTEA,                 -- LSH signature
    code_snippet TEXT,
    license VARCHAR(50),           -- MIT, Apache-2.0, GPL-3.0, etc.
    repo_url VARCHAR(500),
    file_path VARCHAR(500),
    line_start INT,
    line_end INT,
    indexed_at TIMESTAMP
);

CREATE INDEX idx_code_hash ON license_matches(code_hash);
CREATE INDEX idx_license ON license_matches(license);
```

**Data Sources**:
1. GitHub public repos (via BigQuery or GitHub Archive)
2. Open-source package registries (PyPI, NPM, Maven Central)
3. Stack Overflow (CC BY-SA license)

**Update Frequency**: Weekly, incremental updates

### 5.5 Safe Licenses vs Viral Licenses

**Safe** (permissive):
- MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause
- User can use code without open-sourcing their project

**Viral** (copyleft):
- GPL-2.0, GPL-3.0, AGPL-3.0
- Requires derivative works to be open-sourced under same license

**Restricted**:
- CC BY-NC (non-commercial), proprietary licenses
- May require payment or special permissions

**User Setting**:
```yaml
license_policy:
  allow: [MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause]
  warn: [GPL-2.0, GPL-3.0]
  block: [AGPL-3.0, CC-BY-NC, proprietary]
```

---

## 6. Access Control & Authentication

### 6.1 Authentication Methods

#### Individual Developers
- **OAuth 2.0**: GitHub, GitLab, Bitbucket login
- **Email/Password**: With 2FA (TOTP or WebAuthn)

#### Enterprise Teams
- **SAML SSO**: Integrate with Okta, Azure AD, Google Workspace
- **LDAP**: For on-prem Active Directory

### 6.2 Authorization (RBAC)

**Roles**:
- **Developer**: Use all features, access their own data
- **Team Lead**: View team metrics, manage team settings
- **Admin**: Manage org settings, add/remove users, view audit logs
- **Billing**: Manage subscriptions, view invoices

**Permissions**:
```yaml
roles:
  developer:
    - completions:request
    - chat:use
    - refactor:initiate
    - privacy:manage_own
    - data:view_own
    - data:delete_own

  team_lead:
    - completions:request
    - metrics:view_team
    - settings:manage_team
    - privacy:view_team

  admin:
    - users:manage
    - org:manage_settings
    - audit:view_logs
    - billing:view

  billing:
    - billing:manage
    - billing:view_invoices
```

**Implementation** (Policy-as-Code with Casbin):
```go
import "github.com/casbin/casbin/v2"

enforcer, _ := casbin.NewEnforcer("model.conf", "policy.csv")

// Check permission
if enforcer.Enforce(user.ID, "completions", "request") {
    // Allow
} else {
    // Deny
}
```

### 6.3 API Authentication

**JWT Tokens**:
```json
{
  "sub": "user_123",
  "org": "org_456",
  "role": "developer",
  "iat": 1708682880,
  "exp": 1708769280  // 24 hour expiry
}
```

**Signed with RS256** (asymmetric cryptography):
- Private key signs tokens (kept secure on auth server)
- Public key verifies tokens (distributed to all services)

**Token Refresh**:
- Short-lived access tokens (24 hours)
- Long-lived refresh tokens (30 days, stored securely)

### 6.4 Multi-Tenancy Isolation

**Database-Level**:
```sql
-- Every table has org_id
CREATE TABLE completions (
    id BIGSERIAL PRIMARY KEY,
    org_id UUID NOT NULL,  -- Tenant ID
    user_id UUID NOT NULL,
    ...
);

-- Row-Level Security (RLS)
ALTER TABLE completions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON completions
    USING (org_id = current_setting('app.current_org_id')::UUID);
```

**Application-Level**:
```python
# Every query automatically filters by org_id
class CompletionRepository:
    def __init__(self, org_id: UUID):
        self.org_id = org_id

    def find_all(self) -> list[Completion]:
        return db.query(Completion).filter(Completion.org_id == self.org_id).all()
```

---

## 7. Data Encryption

### 7.1 Encryption in Transit

**TLS 1.3** for all network communication:
- IDE ↔ App Server: HTTPS/WSS with TLS 1.3
- App Server ↔ Model Serving: gRPC with TLS
- App Server ↔ Databases: PostgreSQL SSL mode `require`, Redis TLS

**Certificate Management**:
- **Let's Encrypt**: Free, automated certificate issuance and renewal
- **AWS Certificate Manager** (ACM): For AWS deployments
- **Cert-Manager** (Kubernetes): Automates certificate lifecycle

**Cipher Suites** (strong only):
```nginx
ssl_protocols TLSv1.3;
ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';
ssl_prefer_server_ciphers off;
```

### 7.2 Encryption at Rest

**Database Encryption**:
- **PostgreSQL**: Transparent Data Encryption (TDE) or AWS RDS encryption
- **Redis**: AOF/RDB encryption (Redis 6+ with `aclfile`)
- **Elasticsearch**: Encryption at rest via AWS, Azure, or GCP managed services

**Object Storage**:
- **S3**: Server-Side Encryption (SSE-KMS) with customer-managed keys
- **Azure Blob**: Azure Storage Service Encryption with Key Vault
- **MinIO**: Server-side encryption with KMS

**Disk Encryption**:
- **Linux**: LUKS (dm-crypt) for on-prem deployments
- **Cloud**: Default disk encryption (AWS EBS, Azure Disks, GCP Persistent Disks)

### 7.3 Key Management

**Key Hierarchy**:
```
Master Key (Hardware Security Module - HSM)
├─ Data Encryption Key 1 (DEK) - Database
├─ Data Encryption Key 2 (DEK) - Object Storage
└─ Data Encryption Key 3 (DEK) - Backups
```

**Envelope Encryption**:
1. Data encrypted with DEK (fast, symmetric AES-256)
2. DEK encrypted with Master Key (asymmetric, stored in HSM)
3. Encrypted DEK stored with data
4. Master Key never leaves HSM

**Key Rotation**:
- DEKs rotated every 90 days (automated)
- Master Key rotated every 365 days (manual, audited)

---

## 8. Audit Logging

### 8.1 Events to Log

**User Actions**:
- Login/logout (success and failures)
- Privacy mode changes
- Data export/deletion requests
- Consent granted/withdrawn
- Repository added/removed

**System Actions**:
- Model predictions served
- Tool executions (what command, result)
- Policy violations (secrets detected, license matches)
- Configuration changes
- Security incidents

### 8.2 Audit Log Schema

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    org_id UUID,
    user_id UUID,
    action VARCHAR(100) NOT NULL,  -- e.g., 'privacy_mode_changed'
    resource_type VARCHAR(50),     -- e.g., 'repository'
    resource_id VARCHAR(255),
    metadata JSONB,                -- Action-specific details
    ip_address INET,
    user_agent TEXT,
    result VARCHAR(20),            -- success, failure, denied
    INDEX (timestamp),
    INDEX (org_id, timestamp),
    INDEX (user_id, timestamp),
    INDEX (action)
);
```

**Example Entries**:
```sql
INSERT INTO audit_logs (timestamp, org_id, user_id, action, metadata, result)
VALUES
  ('2026-02-23 09:15:00', 'org_123', 'user_456', 'privacy_mode_changed',
   '{"old": "partial", "new": "full", "repo": "company/web-app"}', 'success'),

  ('2026-02-23 09:20:00', 'org_123', 'user_456', 'data_export_requested',
   '{"format": "json", "size_mb": 12.5}', 'success'),

  ('2026-02-23 09:25:00', 'org_123', 'user_789', 'login_failed',
   '{"reason": "invalid_password", "ip": "203.0.113.45"}', 'failure');
```

### 8.3 Immutable Logs

**Write-Only Access**:
- Application can INSERT, cannot UPDATE or DELETE
- Only DBAs with elevated privileges can delete (after retention period)

**Log Shipping**:
- Stream logs to immutable storage (S3 Glacier, AWS CloudWatch Logs, Azure Monitor)
- Enables forensic analysis even if attacker compromises database

**Verification** (Optional, for high-security):
- Cryptographically sign each log entry
- Chain entries (each entry includes hash of previous entry)
- Tamper-evident log (like blockchain)

### 8.4 Log Retention

| Environment | Retention | Storage             |
|-------------|-----------|---------------------|
| Development | 7 days    | PostgreSQL          |
| Staging     | 30 days   | PostgreSQL          |
| Production  | 3 years   | PostgreSQL + S3     |

### 8.5 Log Access

**Who Can Access**:
- **Users**: Their own logs via privacy dashboard
- **Admins**: All logs for their organization
- **Security Team**: All logs for incident response
- **Regulators**: Upon legal request, with proper authorization

**Redaction**:
- Sensitive fields (e.g., code contents) redacted in UI
- Full logs available only to security team and auditors

---

## 9. Incident Response

### 9.1 Incident Types

1. **Data Breach**: Unauthorized access to user data
2. **Service Outage**: System unavailable
3. **Security Vulnerability**: Discovered exploit
4. **Policy Violation**: Secret leaked, license violation missed
5. **Insider Threat**: Malicious employee action

### 9.2 Response Plan

#### Phase 1: Detection (0-15 minutes)
- **Automated Alerts**: Monitoring systems detect anomaly
- **On-Call Engineer**: PagerDuty notifies on-call
- **Initial Assessment**: Severity (P0-P4), impact, urgency

#### Phase 2: Containment (15-60 minutes)
- **Isolate Affected Systems**: Disable compromised accounts, block IPs
- **Stop Data Leakage**: Shut down affected services if necessary
- **Preserve Evidence**: Take snapshots, save logs

#### Phase 3: Investigation (1-24 hours)
- **Root Cause Analysis**: What happened, how, why
- **Scope Determination**: What data accessed, how many users affected
- **Forensics**: Analyze logs, network traffic, system calls

#### Phase 4: Eradication (24-72 hours)
- **Remove Threat**: Patch vulnerabilities, revoke credentials, rebuild systems
- **Verify Clean**: Ensure no backdoors or persistent access

#### Phase 5: Recovery (72 hours - 1 week)
- **Restore Services**: Bring systems back online incrementally
- **Monitor**: Watch for recurrence
- **Communicate**: Update users and stakeholders

#### Phase 6: Post-Mortem (1-2 weeks after)
- **Document Incident**: Timeline, actions taken, lessons learned
- **Implement Fixes**: Long-term improvements to prevent recurrence
- **Update Runbooks**: Refine incident response procedures

### 9.3 GDPR Breach Notification

**Requirement**: Notify authorities within **72 hours** of becoming aware of a breach affecting EU data subjects.

**Notification Process**:
1. Assess if breach meets GDPR threshold (high risk to individuals' rights)
2. Notify national Data Protection Authority (DPA) - for Slovakia: **Úrad na ochranu osobných údajov SR**
3. If high risk, notify affected individuals directly
4. Document breach, response, and mitigation in internal records

**Template**:
```
Subject: Personal Data Breach Notification

Dear Data Protection Authority,

We are notifying you of a personal data breach that occurred on [date].

Nature of the breach: [description]
Categories of data affected: [e.g., email addresses, code snippets]
Number of individuals affected: [approximately X users]
Likely consequences: [impact assessment]
Measures taken: [containment and mitigation steps]
Contact point: [security@company.com]

[Company Name]
[Date]
```

### 9.4 Runbooks

**Example: Suspected Secret Leak**
```markdown
## Runbook: Secret Leak Response

### Symptoms
- Alert: "secret_detected_server" metric spike
- User report of exposed API key

### Immediate Actions (0-15 min)
1. Check audit logs for affected request IDs
2. Identify user(s) and sessions involved
3. Verify secret was redacted before storage
4. If NOT redacted, escalate to P0 incident

### Containment (15-60 min)
1. Disable affected API keys (if customer's)
2. Rotate system secrets (if internal)
3. Review logs to see if secret was used maliciously
4. Notify affected users (if their secret)

### Investigation (1-24 hours)
1. Determine how secret bypassed client-side redaction
2. Check if issue affects other users
3. Review code for similar vulnerabilities

### Eradication (24-72 hours)
1. Deploy fix to client plugin (emergency release)
2. Add server-side validation
3. Add automated test for this scenario

### Post-Mortem
1. Document root cause
2. Update secret redaction patterns
3. Improve monitoring/alerting
```

---

## 10. Compliance Checklist

### 10.1 GDPR Compliance

- [x] Data Processing Agreement (DPA) template created
- [x] Privacy Policy published and user-accessible
- [x] Consent mechanism for Full mode and training data
- [x] Data residency in EU (verified)
- [x] Right of access (data export API)
- [x] Right to erasure (data deletion API)
- [x] Right to data portability (export in JSON/CSV)
- [x] Data retention policies documented and enforced
- [ ] Privacy Impact Assessment (PIA) conducted (scheduled Q3 2026)
- [ ] Data Protection Officer (DPO) appointed (required for large-scale processing)

### 10.2 Security Best Practices

- [x] Encryption in transit (TLS 1.3)
- [x] Encryption at rest (database, object storage)
- [x] Secret detection and redaction (client and server)
- [x] License detection and attribution
- [x] Zero-trust network architecture
- [x] RBAC and least-privilege access
- [x] Audit logging (immutable, 3-year retention)
- [x] Incident response plan documented
- [ ] Third-party security audit (scheduled Q3 2026)
- [ ] Penetration testing (scheduled Q4 2026)
- [ ] Bug bounty program (launch Q4 2026)

### 10.3 Operational Security

- [x] Secrets stored in secret management system (not in code)
- [x] Container images scanned for vulnerabilities
- [x] Dependency scanning (automated PRs for patches)
- [x] Regular secret rotation (90-day cycle)
- [x] Multi-factor authentication (MFA) for all employees
- [x] Security awareness training for engineering team
- [ ] SIEM (Security Information and Event Management) integration (Q3 2026)
- [ ] SOC 2 Type II certification (Q4 2026)

---

## Summary

This document provides comprehensive security and privacy controls for the Copilot-style coding agent:

1. **Privacy Framework**: Three-tier privacy modes (local, partial, full) with user control
2. **EU/GDPR Compliance**: Data residency, user rights, retention policies, DPA
3. **Security Architecture**: Zero-trust, network segmentation, container hardening
4. **Secret Detection**: Client and server-side redaction, user notifications
5. **License Detection**: Exact and fuzzy matching, user warnings for viral licenses
6. **Access Control**: RBAC, multi-tenancy isolation, JWT authentication
7. **Encryption**: TLS 1.3 (transit), AES-256 (rest), key management
8. **Audit Logging**: Immutable logs, 3-year retention, GDPR breach notification
9. **Incident Response**: Detection, containment, investigation, eradication, recovery

**Implementation Priority**:
- **P0 (Launch Blockers)**: Data residency, secret redaction, encryption, user consent
- **P1 (Post-Launch)**: License detection, security audits, compliance certifications
- **P2 (Continuous)**: Monitoring, incident response, training, improvements

**Next Steps**: Review [DEPLOYMENT.md](./DEPLOYMENT.md) for infrastructure setup and [ROADMAP.md](./ROADMAP.md) for implementation timeline.

---

**Document Version**: 1.0
**Last Updated**: February 23, 2026
**Owner**: Slovakia Engineering Team / Security & Compliance
**Review Cycle**: Quarterly or after security incidents
