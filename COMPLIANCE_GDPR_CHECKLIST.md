# EU/GDPR Compliance & Security Checklist

**Jurisdiction:** Slovakia 🇸🇰 (EU)  
**Regulations:** GDPR, eIDAS, Digital Operational Resilience Act (DORA)  
**Date:** 23 Feb 2026  
**Status:** Pre-Implementation Audit

---

## 1. Data Residency & Localization

### Requirement: All personal data in EU

- ✅ **Databricks workspace location:** eu-west-1 (Ireland, EU).
- ✅ **Data Processing Agreement signed:** Databricks EU DPA + SCCs.
- ✅ **Sub-processors approved:**
  | Service | Location | DPA? | Alternative |
  |---------|----------|------|-------------|
  | Databricks | EU (Ireland) | ✅ Signed | N/A |
  | Redis (managed) | EU (Ireland) | ✅ Databricks covers | Self-host in EU |
  | Vector DB (Pinecone) | EU region (Frankfurt) | ⏳ In review | Weaviate/Qdrant self-hosted in EU |
  | GitHub API (PR creation) | US | ✅ SCCs + Standard Contractual Clauses | GitLab (EU) alternative |

**Action Items:**
- [ ] Confirm Pinecone EU region available (sign DPA).
- [ ] If Pinecone unavailable, provision self-hosted Qdrant in EU.
- [ ] Document all data flows in system architecture diagram.
- [ ] Legal sign off on SCCs for US processors (GitHub).

**Responsible:** Data Protection Officer + Legal  
**Due:** 20 Feb 2026

---

## 2. Data Subject Rights (GDPR Articles 12–22)

### Right to Access (Article 15)

**What:** User can request all personal data held about them.

**Implementation:**
```python
# app_server/gdpr.py
class GDPRController:
    def export_user_data(self, user_id: str) -> dict:
        """Export all personal data for user (right to access)."""
        
        data = {
            "telemetry": self.db.query(f"""
                SELECT * FROM completions 
                WHERE user_id_hash = {hash_user(user_id)}
            """),
            "tasks": self.db.query(f"""
                SELECT * FROM tasks 
                WHERE user_id_hash = {hash_user(user_id)}
            """),
            "training_consent": self.db.query(f"""
                SELECT * FROM training_consent 
                WHERE user_id = {user_id}
            """),
            "deletion_requests": self.db.query(f"""
                SELECT * FROM deletion_log 
                WHERE user_id = {user_id}
            """)
        }
        
        # Return as JSON (machine-readable)
        return json.dumps(data, indent=2)
    
    @app.post("/api/v1/gdpr/access-request")
    async def request_access(user = Depends(get_current_user)):
        """User requests export of their data."""
        data = gdpr.export_user_data(user.id)
        
        # Send as file download
        return FileResponse(
            io.BytesIO(data.encode()),
            filename=f"my_data_{user.id}_{date.today()}.json",
            media_type="application/json"
        )
```

**Timeline:** Respond within 30 days (GDPR requirement).

- [ ] Implement /api/v1/gdpr/access-request endpoint.
- [ ] Test: request data, verify completeness within 48 hours.

**Due:** Month 2

---

### Right to Erasure (Article 17, "Right to be Forgotten")

**What:** User can request deletion of their personal data (exceptions: legal obligation, etc.).

**Implementation:**
```python
# app_server/gdpr.py
@app.post("/api/v1/gdpr/deletion-request")
async def request_deletion(user = Depends(get_current_user)):
    """User requests deletion of their personal data."""
    
    # Log deletion request (audit trail)
    self.db.insert("deletion_requests", {
        "user_id": user.id,
        "requested_at": now(),
        "requested_by": user.email,
        "ip_address": request.client.host
    })
    
    # Schedule async deletion (within 30 days)
    schedule_deletion_task(user.id, days=30)
    
    return {
        "status": "deletion_scheduled",
        "completed_by": (now() + timedelta(days=30)).isoformat()
    }

async def delete_user_data(user_id: str):
    """Delete all personal data for user (30-day grace period)."""
    
    # Soft delete: mark rows as deleted
    self.db.execute(f"""
        UPDATE completions SET deleted_flag = true 
        WHERE user_id_hash = {hash_user(user_id)}
    """)
    
    self.db.execute(f"""
        UPDATE tasks SET deleted_flag = true 
        WHERE user_id_hash = {hash_user(user_id)}
    """)
    
    # Hard delete: permanent removal (60 days later for audit purposes)
    schedule_hard_delete(user_id, days=60)
    
    # Update training_consent, deletion_log
    self.db.execute(f"""
        DELETE FROM training_consent WHERE user_id = {user_id}
    """)
    
    logger.info(f"✅ User {user_id} data deleted (soft). Hard delete scheduled in 60 days.")
```

**Timeline:** Soft delete within 30 days; hard delete within 60 days.

- [ ] Implement /api/v1/gdpr/deletion-request endpoint.
- [ ] Verify soft-delete doesn't affect business/audit logs.
- [ ] Schedule hard-delete job (cron, tested).

**Due:** Month 2–3

---

### Right to Data Portability (Article 20)

**What:** User can request their data in portable format (JSON, CSV).

**Implementation:**
```python
@app.post("/api/v1/gdpr/portability-request")
async def request_portability(format: str = "json", user = Depends(get_current_user)):
    """Export user data in portable format (JSON/CSV)."""
    
    if format == "json":
        data = gdpr.export_user_data(user.id)
        return FileResponse(
            io.BytesIO(data.encode()),
            filename=f"my_data_{format}.json"
        )
    
    elif format == "csv":
        # Export completions + tasks to CSV
        completions_csv = gdpr.export_completions_csv(user.id)
        tasks_csv = gdpr.export_tasks_csv(user.id)
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            zf.writestr("completions.csv", completions_csv)
            zf.writestr("tasks.csv", tasks_csv)
        
        buffer.seek(0)
        return FileResponse(
            buffer,
            filename=f"my_data_{user.id}.zip",
            media_type="application/zip"
        )
```

- [ ] Export endpoints tested (JSON, CSV).
- [ ] Verify data format is machine-readable & complete.

**Due:** Month 2

---

### Right to Object & Opt-Out (Article 21)

**What:** User can opt-out of training their data being used to improve the model.

**Checkbox in UI:**
```
Privacy Settings
━━━━━━━━━━━━━━━━━━━━━━━
☑ Allow training on my code (improves model)
     [Learn more]

☑ Allow telemetry collection (helps us debug)
     [Learn more]

☑ Allow sales & marketing to contact me
     [Opt-out]
```

**Implementation:**
```python
class ConsentManager:
    def set_training_consent(self, user_id: str, enabled: bool):
        """User opt-in/out of training."""
        self.db.insert("training_consent", {
            "user_id": user_id,
            "training_allowed": enabled,
            "timestamp": now(),
            "ip_address": request.client.host
        })
        
        if not enabled:
            # Remove from training queue immediately
            self.training_queue.remove_user(user_id)
```

- [ ] UI checkbox implemented.
- [ ] Verify opted-out users excluded from retraining.

**Due:** Month 1

---

## 3. Consent & Transparency

### Privacy Policy & Terms

**Must include:**
- ✅ What data is collected? (completions, telemetry, code snippets)
- ✅ Why? (model improvement, debugging, safety)
- ✅ Who has access? (ML team for training, Security for audits)
- ✅ How long retained? (completions: 30 days; telemetry: 1 year; training data: 2 years; audit logs: 7 years)
- ✅ User rights (access, delete, portability)
- ✅ Sub-processor list

**Annual review:** ✅ Yes, required under GDPR.

- [ ] Privacy policy drafted by Legal.
- [ ] Published on company website.
- [ ] Users must click "Accept" before using tool.
- [ ] Terms version tracked in telemetry (for disputes).

**Due:** 25 Feb 2026

---

### Organizational Consent (for private repos)

**When:** Training on private repo code requires explicit org-level consent.

**Form:**
```
Organization Training Consent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
By enabling training, you allow the Copilot Coding Agent to use 
code from your repositories to improve model quality.

Your data will:
✓ Be stored in EU only (Ireland)
✓ Be anonymized & never shared with 3rd parties
✓ Be deleted on request (30 days)
✓ Be excluded from fine-tuning if you revoke consent

☑ I authorize my organization to opt-in to training
   Organization: _______________
   Contact: _______________
   
   [APPROVE & SIGN] [CANCEL]
```

**Implementation:**
```python
class OrganizationConsent:
    def get_consent_status(self, org_id: str) -> bool:
        """Check if org consented to training."""
        record = self.db.query(f"""
            SELECT * FROM org_training_consent 
            WHERE org_id = {org_id} AND status = 'APPROVED'
        """)
        return bool(record)
    
    def approve_consent(self, org_id: str, authorized_by: str):
        """Org approves training consent."""
        self.db.insert("org_training_consent", {
            "org_id": org_id,
            "status": "APPROVED",
            "authorized_by": authorized_by,
            "signed_date": now(),
            "effective_date": now()
        })
        
        # Log for audit
        audit_log.insert({
            "event": "org_training_consent_approved",
            "org_id": org_id,
            "timestamp": now()
        })
```

- [ ] Consent form UI implemented.
- [ ] Org admin can sign digitally.
- [ ] Audit trail maintained.

**Due:** Month 1

---

## 4. Data Security & Encryption

### At Rest

**Requirement:** AES-256 encryption for all PII / code data.

**Implementation:**
```python
# app_server/encryption.py
from cryptography.fernet import Fernet
import os

class DataEncryption:
    def __init__(self):
        # Load key from Databricks secret scope (not in code)
        key = dbutils.secrets.get("copilot", "encryption_key")
        self.cipher = Fernet(key)
    
    def encrypt_code(self, code: str) -> str:
        """Encrypt code before storing in DB."""
        return self.cipher.encrypt(code.encode()).decode()
    
    def decrypt_code(self, encrypted: str) -> str:
        """Decrypt code from DB."""
        return self.cipher.decrypt(encrypted.encode()).decode()

# Usage in telemetry
telemetry = {
    "code_snippet": encrypt(completion),  # Encrypted in DB
    "user_id_hash": hash_user(user_id),   # Hashed, never decrypted
    "timestamp": now()
}
```

- [ ] Encryption key stored in Databricks secrets (never in code).
- [ ] All code/PII fields encrypted in DB.
- [ ] Test: verify encrypted data unreadable without key.

**Due:** Month 1–2

---

### In Transit

**Requirement:** TLS 1.3, perfect forward secrecy.

**Implementation:**
```yaml
# app_server/nginx.conf (reverse proxy)
ssl_protocols TLSv1.3;
ssl_ciphers HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 24h;

# HSTS: force HTTPS for 1 year
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

- [ ] TLS 1.3 enforced.
- [ ] Certificate valid (Let's Encrypt auto-renewal).
- [ ] HSTS header set.

**Due:** Month 1

---

## 5. Audit Logging & Compliance Reporting

### Audit Log Requirements

**Must log:**
- User authentication (login, logout, token refresh).
- Data access (query for user data, export).
- Authorization changes (consent toggles, permission grants).
- Tool invocations (test run, PR creation, linter calls).
- Security events (failed login, redaction triggered, unsafe code detected).

**Example log entry:**
```json
{
  "timestamp": "2026-02-23T09:30:00Z",
  "event_id": "evt_abc123",
  "event_type": "tool_invocation",
  "user_id_hash": "user_abc_hashed",
  "action": "run_test",
  "resource": "pytest src/tests/",
  "status": "success",
  "result": {"exit_code": 0, "passed": 42},
  "ip_address": "10.0.0.1",
  "duration_ms": 2300
}
```

**Retention:** 7 years (for compliance audits).

- [ ] Audit logging module implemented.
- [ ] All events logged with timestamp, user, action.
- [ ] Read-only audit table (prevent tampering).

**Due:** Month 2

---

### Compliance Reports (Automated)

**Monthly GDPR report:**
```python
# compliance/gdpr_report.py
def generate_gdpr_report(month: int, year: int) -> dict:
    """Generate monthly GDPR compliance report."""
    
    report = {
        "month": f"{month}/{year}",
        "data_subjects": count_unique_users(),  # How many users?
        "access_requests": count_access_requests(),  # Any data access requests?
        "deletion_requests": count_deletion_requests(),  # Any deletes?
        "consent_changes": count_consent_toggles(),  # Opt-in/out?
        "data_breaches": count_security_incidents(),  # Any incidents?
        "data_flows": {
            "code_sent_to_model": total_code_bytes_sent,
            "training_samples_used": training_samples_count,
            "stored_in_eu": verify_all_in_eu()
        }
    }
    
    return report
```

- [ ] Report auto-generated monthly.
- [ ] Sent to Data Protection Officer.
- [ ] Shared with CTO/Legal monthly.

**Due:** Month 3+

---

## 6. Incident Response & Data Breach Notification

### Data Breach Protocol

**If breach detected:**

1. **Within 24 hours:**
   - [ ] Incident response team activated.
   - [ ] Scope assessed (how much data? whose?)
   - [ ] Immediate mitigation (isolate affected systems).

2. **Within 72 hours (GDPR requirement):**
   - [ ] Notify Data Protection Officer.
   - [ ] Notify affected users (if high risk).
   - [ ] File report with Slovak Data Protection Authority (UDOP).

3. **Within 30 days:**
   - [ ] Full incident report published.
   - [ ] Remediation steps documented.
   - [ ] Post-mortem completed.

**Contact info:**
| Role | Name | Email | On-Call? |
|------|------|-------|---------|
| Data Protection Officer | [NAME] | dpo@company.com | ✅ 24/7 |
| Security Lead | [NAME] | security@company.com | ✅ 24/7 |
| Legal Counsel | [NAME] | legal@company.com | Business hrs |

- [ ] Incident response playbook drafted.
- [ ] On-call rotation set up.
- [ ] Contact list updated.

**Due:** Month 1

---

## 7. Third-Party & Vendor Management

### Sub-Processor Audit

**Databricks (model serving, inference):**
- [ ] DPA signed? ✅ Yes
- [ ] SOC 2 Type II? ✅ Yes
- [ ] Data location? EU (Ireland)
- [ ] Encryption? ✅ At rest & in transit
- [ ] Audit frequency? Annual external audit

**Vector DB (Pinecone or Qdrant):**
- [ ] EU region available? ⏳ Confirm
- [ ] DPA signed? ⏳ Pending
- [ ] Data location? EU (to be confirmed)

**GitHub (PR creation):**
- [ ] Location? US (requires SCCs)
- [ ] SCCs signed? ⏳ Pending
- [ ] Data minimization? Only repo name, PR title (no code)

### Processor change control

When adding a new third-party (e.g., analytics vendor):

```python
# compliance/vendor_management.py
def approve_new_processor(vendor_name: str, purpose: str, location: str):
    """Approve new processor with DPA verification."""
    
    # Checklist
    required_docs = [
        "Data Processing Agreement (DPA)",
        "Privacy Policy",
        "SOC 2 / ISO 27001 Certification",
        "Standard Contractual Clauses (if non-EU)"
    ]
    
    for doc in required_docs:
        if not has_doc(vendor_name, doc):
            raise Exception(f"Missing: {doc}")
    
    # Log approval
    audit_log.insert({
        "event": "processor_approved",
        "vendor": vendor_name,
        "approved_by": current_user.id,
        "timestamp": now()
    })
```

- [ ] Vendor approval process defined.
- [ ] DPA template available for new vendors.
- [ ] Annual vendor audit schedule set.

**Due:** Month 1

---

## 8. Technical Security (Infrastructure)

### Vulnerability Scanning

**Automated SAST (Static Analysis):**
- [ ] Setup GitHub advanced security / SonarQube.
- [ ] Scan on every PR -> block if critical vulns.

**Dependency scanning:**
- [ ] Setup Dependabot / Snyk.
- [ ] Auto-patch low-risk updates.
- [ ] Alert on high-risk vulns.

**Container scanning:**
- [ ] Scan Docker image for vulns → Aqua / Trivy.
- [ ] Only deploy images with 0 critical vulns.

- [ ] SAST enabled on first PR.
- [ ] Dependency scanner activated.
- [ ] Container scanning in CI/CD.

**Due:** Month 1

---

### Penetration Testing

**Schedule:** Annual (first: Month 6+1 = Month 7).

**Scope:**
- App Server API (auth bypass, injection attacks).
- IDE plugin (supply chain, phishing).
- Data stores (encryption, access control).
- Sandbox escape scenarios.

- [ ] Pen test vendor selected.
- [ ] Rules of engagement documented.
- [ ] Test scheduled for April 2026.

**Due:** Month 6–7

---

## 9. Training & Awareness

### Security training (all team)

- [ ] GDPR fundamentals (2 hours, annual).
- [ ] Data minimization best practices.
- [ ] Password management & 2FA.

### DPA-specific training (data handlers)

- [ ] Data processors vs controllers.
- [ ] Sub-processor obligations.
- [ ] Data subject rights (access, delete).

- [ ] Training module created.
- [ ] All team members complete by Month 1.
- [ ] Annual refresher scheduled.

**Due:** Month 1

---

## 10. Compliance Checklist (Pre-Launch)

### Legal & Governance

- [ ] Privacy Policy finalized & approved by Legal.
- [ ] Data Processing Agreement signed (Databricks).
- [ ] Standard Contractual Clauses (GitHub API).
- [ ] Organization consent form approved.
- [ ] Incident response playbook drafted.

### Technical Security

- [ ] TLS 1.3 enabled (in-transit encryption).
- [ ] AES-256 encryption (at-rest).
- [ ] Secrets redaction engine tested (100% coverage).
- [ ] Audit logging operational.
- [ ] Backup & disaster recovery tested.

### Data Subject Rights

- [ ] /api/v1/gdpr/access-request working.
- [ ] /api/v1/gdpr/deletion-request working.
- [ ] /api/v1/gdpr/portability-request working.
- [ ] Opt-out interface functional.

### Monitoring & Response

- [ ] Security  monitoring 24/7 (anomaly detection, rate limit).
- [ ] On-call schedule established.
- [ ] Incident response playbook tested.
- [ ] DPO contact updated.

### Documentation

- [ ] Data flow diagram (showing EU residency).
- [ ] Sub-processor list updated.
- [ ] Compliance matrix (GDPR checklist).
- [ ] Retention schedule specified.

### Audits & Attestations

- [ ] Internal compliance audit passed.
- [ ] 3rd-party security audit scheduled (Q3).
- [ ] SOC 2 / ISO 27001 roadmap defined.

---

## Sign-Off

**Compliance Review Board:**

| Role | Name | Date | Sign |
|------|------|------|------|
| Data Protection Officer | __________ | _____ | _____ |
| Legal Counsel | __________ | _____ | _____ |
| Security Lead | __________ | _____ | _____ |
| CTO | __________ | _____ | _____ |

**Approved for:  ☐ Pilot (Month 1)    ☐ Production (Q3 2026)**

---

**Last Updated:** 23 Feb 2026  
**Next Review:** 30 April 2026 (post-pilot)

