# 🛡️ GDPR / DSGVO Compliance Guide
## AI Customer Churn & Behavioral Analytics Platform

**Version:** 1.0.0  
**DPO Contact:** dpo@churn-analytics.example.com  
**Legal Basis:** GDPR (EU) 2016/679 + BDSG (Germany) + DSG (Austria/Switzerland)  
**Last Review:** 2024-01-01

---

## 1. Data Processing Principles (Art. 5 GDPR)

| Principle | Implementation |
|-----------|----------------|
| **Lawfulness** | Consent + Legitimate interest (fraud prevention) |
| **Purpose limitation** | Data used only for churn/analytics — enforced at code level |
| **Data minimisation** | Only fields needed for ML features are processed |
| **Accuracy** | Data validation pipeline + customer correction API |
| **Storage limitation** | Automated retention policy (see §6) |
| **Integrity & Confidentiality** | AES-256 at rest, TLS 1.3 in transit, CMK |
| **Accountability** | Immutable audit logs, DPA documentation |

---

## 2. Legal Basis for Processing

| Processing Activity | Legal Basis | Article |
|---------------------|-------------|---------|
| Churn prediction | Legitimate interest (Art. 6(1)(f)) | 6(1)(f) |
| Behavioral analytics | Consent | 6(1)(a) |
| Fraud/anomaly detection | Legitimate interest + legal obligation | 6(1)(c)(f) |
| Marketing retention offers | Consent | 6(1)(a) |
| GenAI risk summaries | Legitimate interest | 6(1)(f) |

**Consent Management:**
```python
# All data processing is gated by consent check
# See: api/services/gdpr_service.py → check_processing_consent()
```

---

## 3. Data Subject Rights Implementation

### Art. 15 — Right of Access
```
GET /gdpr/customer/{customer_id}/data-export
→ Returns: all personal data held, processing purposes, retention dates
→ Format: JSON + PDF export
→ Response time: ≤ 30 days (automated: ≤ 24h)
```

### Art. 16 — Right to Rectification
```
PUT /gdpr/customer/{customer_id}/correct
→ Updates: customer profile + re-triggers ML features
→ Audit: logs correction event with timestamp + operator ID
```

### Art. 17 — Right to Erasure ("Right to be Forgotten")
```
DELETE /gdpr/customer/{customer_id}
→ Triggers: delete_customer_data.py workflow
→ Steps:
   1. Verify identity + consent withdrawal
   2. Pseudonymise audit logs (retain for legal obligation)
   3. Delete from: Azure SQL, ADLS, Redis cache, Cosmos DB
   4. Trigger ML model feature removal
   5. Confirm deletion receipt (email + API response)
→ Completion: ≤ 30 days (automated: ≤ 72h)
```

### Art. 18 — Right to Restriction
```
POST /gdpr/customer/{customer_id}/restrict-processing
→ Flags customer record → excludes from all ML scoring
→ Data retained but not processed
```

### Art. 20 — Right to Portability
```
GET /gdpr/customer/{customer_id}/portable-export
→ Format: machine-readable JSON (ISO 20022 compatible)
→ Includes: all personal data + consent history
```

### Art. 21 — Right to Object
```
POST /gdpr/customer/{customer_id}/object-processing
→ Stops: automated profiling, churn scoring, GenAI summaries
→ Exception: fraud detection (legitimate interest override)
```

### Art. 22 — Right Not to Be Subject to Automated Decisions
```
POST /gdpr/customer/{customer_id}/request-human-review
→ Routes to: human agent queue for manual review
→ No fully automated decisions with legal effect on customers
→ All churn actions require human approval before execution
```

---

## 4. PII Masking Implementation

### 4.1 PII Categories in Scope

| Category | Fields | Masking Method |
|----------|--------|----------------|
| Name | first_name, last_name | SHA-256 tokenization |
| Contact | email, phone | AES-256 encryption |
| Identity | IBAN, account_no | Format-preserving encryption (FPE) |
| Address | street, city, postal_code | Pseudonymisation |
| Device | IP address, device_id | Hashing + salt |
| Behavioral | clickstream, location | Aggregation / k-anonymity |

### 4.2 Masking Pipeline

```python
# middleware/pii_masking.py
# Applied automatically on all API responses

PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "german_phone": r"(\+49|0)[0-9]{10,12}",
    "iban": r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}",
    "ip_address": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
}

# ML features use ONLY anonymised/aggregated data
# Raw PII never enters ML training pipeline
```

### 4.3 Tokenization Flow

```
RAW PII → HMAC-SHA256(value + salt) → PSEUDONYMOUS TOKEN
                                            │
                        Stored in Key Vault ←┘ (salt secret)
                        Token used in DB, ML, API responses
```

---

## 5. Consent Management

### Consent Record Schema
```json
{
  "customer_token": "sha256_hashed_id",
  "consent_version": "2024-01-01-v2",
  "purposes": {
    "churn_analytics": true,
    "behavioral_profiling": false,
    "marketing_contact": true,
    "data_sharing_third_parties": false,
    "genai_processing": true
  },
  "recorded_at": "2024-01-15T10:30:00Z",
  "channel": "web_portal",
  "ip_hash": "a3f2...",
  "consent_text_version": "privacy-policy-v3.2"
}
```

### Consent Gate in Code
```python
# Every data access checks consent
async def check_processing_consent(customer_id: str, purpose: str) -> bool:
    consent = await db.get_consent(customer_id)
    if not consent or not consent.purposes.get(purpose, False):
        raise ConsentNotGrantedError(
            f"Customer {customer_id[:8]}... has not consented to {purpose}"
        )
    return True
```

---

## 6. Data Retention Policy

| Data Category | Retention Period | Legal Basis | Action on Expiry |
|---------------|-----------------|-------------|-----------------|
| Customer profile | Contract duration + 3 years | HGB §257 | Auto-delete |
| Transaction records | 10 years | AO §147 (tax) | Archive → delete |
| Audit logs (GDPR) | 3 years | GDPR Art. 5(2) | Pseudonymise → keep |
| ML training data | 2 years | Internal policy | Delete + retrain |
| Anomaly events | 5 years | BaFin requirement | Archive |
| Consent records | Indefinite (until withdrawal) | GDPR Art. 7 | Keep proof |
| Churn scores | 1 year rolling | Internal policy | Auto-delete |

### Automated Retention Enforcement
```bash
# Runs nightly via Azure Data Factory / GitHub Actions
python scripts/data_retention_cleanup.py --dry-run  # preview
python scripts/data_retention_cleanup.py --execute  # enforce
```

---

## 7. Data Protection Impact Assessment (DPIA)

**Required under:** GDPR Art. 35 (high-risk processing with AI profiling)

### Risk Assessment Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Unauthorized ML profiling | Low | High | Consent gates + RBAC |
| Data breach (PII exposure) | Low | Critical | AES-256 + network isolation |
| Discriminatory AI decisions | Medium | High | Fairness audits + human review |
| Purpose creep | Low | Medium | Code-level purpose enforcement |
| Third-party data sharing | Low | High | Data processing agreements |
| Model inversion attack | Very Low | High | Differential privacy (future) |

### Residual Risk: **ACCEPTABLE** (with mitigations applied)

---

## 8. RBAC & Access Control

### Role Definitions
```yaml
roles:
  platform-admin:
    - Full access to all resources
    - Can manage RBAC assignments
    - Azure AD group: sg-churn-platform-admins

  ml-engineer:
    - Read/write to Databricks, MLflow
    - Read anonymised training data
    - No access to raw PII
    - Azure AD group: sg-churn-ml-engineers

  api-consumer:
    - POST /churn/predict
    - GET /segmentation/customer/{id}
    - GET /retention/recommend/{id}
    - No GDPR endpoints
    - Azure AD group: sg-churn-api-consumers

  bi-analyst:
    - Read aggregated Power BI datasets
    - No individual-level data access
    - Azure AD group: sg-churn-bi-analysts

  gdpr-officer:
    - All /gdpr/* endpoints
    - Audit log access
    - No ML model access
    - Azure AD group: sg-churn-dpo

  auditor:
    - Read-only audit logs
    - No data modification
    - Azure AD group: sg-churn-auditors
```

---

## 9. Audit Logging

### Audit Event Schema
```json
{
  "event_id": "uuid-v4",
  "timestamp": "ISO-8601",
  "event_type": "DATA_ACCESS | DATA_MODIFICATION | GDPR_REQUEST | AUTH_EVENT",
  "actor": {
    "user_id": "azure_ad_object_id",
    "role": "ml-engineer",
    "ip_hash": "hmac_hashed"
  },
  "resource": {
    "type": "customer_profile",
    "id_token": "pseudonymous_token",
    "action": "READ"
  },
  "outcome": "SUCCESS | FAILURE | DENIED",
  "correlation_id": "request_uuid",
  "gdpr_basis": "legitimate_interest"
}
```

### Audit Log Immutability
- Stored in Azure Immutable Blob Storage (WORM policy)
- 3-year retention lock
- Cryptographic hash chain (tamper detection)
- Exported nightly to Azure Monitor Log Analytics

---

## 10. Third-Party Data Processing

### Data Processing Agreements (DPA) Required

| Vendor | Service | DPA Status | Data Shared |
|--------|---------|-----------|-------------|
| Microsoft Azure | Infrastructure | ✅ Signed | Encrypted data |
| Azure OpenAI | GPT-4o | ✅ Signed | Anonymised text |
| Databricks | ML platform | ✅ Signed | Anonymised features |
| Power BI | Reporting | ✅ Signed | Aggregated metrics |

**Standard Contractual Clauses (SCCs):** Required for any non-EU data transfers.  
**US data transfers:** Covered under EU-US Data Privacy Framework.

---

## 11. Security Incident Response

### GDPR Breach Notification (Art. 33/34)

```
INCIDENT DETECTED
      │
      ▼ (0-1h)
CLASSIFY: Personal data breach? Yes/No
      │ Yes
      ▼ (1-4h)
ASSESS: Risk to individuals (low/medium/high/critical)
      │
      ▼ (4-24h)
NOTIFY DPA: ≤ 72 hours (Art. 33) → send to relevant DPA
      │ (if high risk to individuals)
      ▼ (24-48h)
NOTIFY CUSTOMERS: without undue delay (Art. 34)
      │
      ▼ (ongoing)
REMEDIATE + DOCUMENT → update DPIA → post-mortem
```

**Notification contacts:**
- Germany: Bundesbeauftragter für Datenschutz (BfDI)
- Austria: Datenschutzbehörde (DSB)
- Switzerland: Eidgenössischer Datenschutzbeauftragter (EDÖB)

---

## 12. Delete Customer Data Workflow

```bash
# GDPR Art. 17 — Automated erasure
python scripts/delete_customer_data.py \
  --customer-token <sha256_token> \
  --reason "customer_request" \
  --requested-by "dpo@company.com"

# This script:
# 1. Validates customer token exists
# 2. Checks no active legal hold
# 3. Deletes from Azure SQL (all tables)
# 4. Deletes from ADLS (all partitions)
# 5. Purges Redis cache
# 6. Removes from Cosmos DB
# 7. Flags ML feature store (excludes from future training)
# 8. Pseudonymises audit logs (retains for compliance)
# 9. Sends deletion confirmation
# 10. Records in GDPR register
```

---

## 13. Privacy by Design Checklist

- [x] PII masking applied before any data enters ML pipeline
- [x] Consent checked before every processing operation
- [x] Minimum data collection (no unnecessary fields)
- [x] Pseudonymisation by default for analytical workloads
- [x] Automated retention enforcement
- [x] RBAC enforced at API + database + storage layer
- [x] All secrets in Azure Key Vault (no hardcoded credentials)
- [x] Encrypted storage (AES-256, CMK)
- [x] Immutable audit trail
- [x] Human review required for decisions affecting customers
- [x] Regular bias/fairness audits on ML models
- [x] DPIA documented and maintained
- [x] Third-party DPAs in place
- [x] Breach notification procedure documented
