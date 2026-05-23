# 📅 Agile Sprint Planning
## AI Customer Churn & Behavioral Analytics Platform

**Methodology:** Scrum  
**Sprint Duration:** 2 weeks  
**Team Size:** 6 engineers  
**Velocity Target:** 40 story points / sprint  
**Start Date:** 2024-01-08  
**Release Target:** v1.0.0 → 2024-06-28

---

## 📌 Definition of Done (DoD)

A story is DONE when:
- [ ] Code written, reviewed (2 approvals), merged to `main`
- [ ] Unit tests written (≥ 85% coverage on changed code)
- [ ] Integration tests pass in CI
- [ ] Security scan passes (no HIGH/CRITICAL findings)
- [ ] GDPR impact reviewed (by DPO for data-touching stories)
- [ ] API documentation updated (OpenAPI spec)
- [ ] Deployed to staging, smoke-tested
- [ ] Acceptance criteria verified by Product Owner

---

## 🎯 Product Backlog (Prioritised)

### EPIC 1: Core ML Infrastructure
| ID | Story | Points | Priority |
|----|-------|--------|----------|
| E1-S1 | As an ML engineer, I can run EDA on DACH customer data in Databricks | 5 | P0 |
| E1-S2 | As an ML engineer, I can build a feature engineering pipeline (RFM, engagement, payment scores) | 8 | P0 |
| E1-S3 | As an ML engineer, I can train a churn prediction model with XGBoost + LightGBM ensemble | 13 | P0 |
| E1-S4 | As an ML engineer, I can register models in MLflow with full metadata | 5 | P0 |
| E1-S5 | As an ML engineer, I can train a KMeans segmentation model with RFM features | 8 | P0 |
| E1-S6 | As an ML engineer, I can train an Isolation Forest anomaly detection model | 8 | P1 |
| E1-S7 | As an ML engineer, I can evaluate models with fairness/bias audit (SHAP + disparate impact) | 8 | P1 |
| E1-S8 | As an ML engineer, I can detect model drift using PSI and trigger alerts | 5 | P1 |

### EPIC 2: FastAPI Backend
| ID | Story | Points | Priority |
|----|-------|--------|----------|
| E2-S1 | As a developer, I can set up a production FastAPI app with health checks and versioning | 3 | P0 |
| E2-S2 | As a developer, I can implement JWT + Azure AD authentication with RBAC | 8 | P0 |
| E2-S3 | As a developer, I can implement PII masking middleware (auto-redact API responses) | 8 | P0 |
| E2-S4 | As a developer, I can implement immutable audit logging for all data access events | 5 | P0 |
| E2-S5 | As an API consumer, I can POST a customer ID and get a churn probability score | 8 | P0 |
| E2-S6 | As an API consumer, I can GET a customer's segment classification | 5 | P0 |
| E2-S7 | As an API consumer, I can POST transaction data and get an anomaly score | 8 | P1 |
| E2-S8 | As an API consumer, I can GET personalised retention recommendations | 8 | P1 |
| E2-S9 | As an API consumer, I can GET a GenAI business explanation of why a customer may churn | 8 | P1 |
| E2-S10 | As a DPO, I can DELETE a customer's data via the GDPR erasure endpoint | 8 | P0 |
| E2-S11 | As a DPO, I can GET a customer's consent record and data export | 5 | P0 |
| E2-S12 | As a developer, I can run batch churn predictions for 10K customers | 5 | P2 |

### EPIC 3: Data Infrastructure
| ID | Story | Points | Priority |
|----|-------|--------|----------|
| E3-S1 | As a data engineer, I can ingest customer data into Bronze/Silver/Gold layers in ADLS | 8 | P0 |
| E3-S2 | As a data engineer, I can implement automated PII masking on data ingestion | 8 | P0 |
| E3-S3 | As a data engineer, I can set up Azure SQL schema for churn scores, segments, audit logs | 5 | P0 |
| E3-S4 | As a data engineer, I can implement data retention policy with automated cleanup | 5 | P1 |
| E3-S5 | As a data engineer, I can implement streaming feature computation with Delta Live Tables | 8 | P2 |

### EPIC 4: GenAI / RAG
| ID | Story | Points | Priority |
|----|-------|--------|----------|
| E4-S1 | As a product manager, I can get a plain-language explanation of why a customer is at churn risk | 8 | P1 |
| E4-S2 | As a retention manager, I can get a GenAI-generated personalised retention action plan | 8 | P1 |
| E4-S3 | As an exec, I can get a C-suite customer risk narrative (no PII, aggregated) | 5 | P2 |
| E4-S4 | As a developer, I can implement RAG with Azure Cognitive Search + customer knowledge base | 13 | P1 |

### EPIC 5: Power BI Dashboards
| ID | Story | Points | Priority |
|----|-------|--------|----------|
| E5-S1 | As an exec, I can see the monthly churn rate trend with forecast | 5 | P0 |
| E5-S2 | As a retention manager, I can see a high-risk customer heatmap by segment | 5 | P0 |
| E5-S3 | As a BI analyst, I can see customer segment distribution with RFM profiles | 5 | P1 |
| E5-S4 | As an operations manager, I can see real-time anomaly trends and affected counts | 5 | P1 |
| E5-S5 | As an exec, I can see revenue-at-risk (churning CLV × churn probability) | 8 | P0 |
| E5-S6 | As an ML engineer, I can see model health: AUC trend, confidence distribution, drift alerts | 5 | P1 |
| E5-S7 | As a retention manager, I can see retention campaign success rate and ROI | 5 | P2 |

### EPIC 6: GDPR & Security
| ID | Story | Points | Priority |
|----|-------|--------|----------|
| E6-S1 | As a DPO, I can run an automated GDPR Art.17 data erasure for a customer | 8 | P0 |
| E6-S2 | As a DPO, I can export all data held on a customer (Art. 15 access) | 5 | P0 |
| E6-S3 | As a DPO, I can record and query customer consent by purpose | 5 | P0 |
| E6-S4 | As a security engineer, I can verify all secrets are stored in Azure Key Vault | 3 | P0 |
| E6-S5 | As a security engineer, I can run SAST/DAST scans in CI with zero HIGH findings | 5 | P0 |
| E6-S6 | As a compliance officer, I can view immutable audit logs for any customer data access | 5 | P0 |
| E6-S7 | As a DPO, I can apply data retention policy that auto-deletes expired records | 5 | P1 |

### EPIC 7: DevOps & CI/CD
| ID | Story | Points | Priority |
|----|-------|--------|----------|
| E7-S1 | As a developer, I can run the full platform locally with docker-compose | 3 | P0 |
| E7-S2 | As a developer, CI runs on every PR: lint, test, security scan, build | 5 | P0 |
| E7-S3 | As a DevOps engineer, CD deploys to staging on merge to main | 5 | P1 |
| E7-S4 | As a DevOps engineer, CD deploys to production after manual approval | 5 | P1 |
| E7-S5 | As a DevOps engineer, Azure Bicep IaC provisions all infrastructure | 8 | P1 |

### EPIC 8: Testing & QA
| ID | Story | Points | Priority |
|----|-------|--------|----------|
| E8-S1 | As QA, all API endpoints have unit tests (≥85% coverage) | 8 | P0 |
| E8-S2 | As QA, ML model meets minimum accuracy thresholds (AUC ≥ 0.85) | 5 | P0 |
| E8-S3 | As QA, GDPR compliance tests verify all data subject rights work | 5 | P0 |
| E8-S4 | As QA, security tests verify auth, RBAC, and injection resistance | 5 | P0 |
| E8-S5 | As QA, bias/fairness tests confirm no disparate impact | 5 | P1 |
| E8-S6 | As QA, model drift tests verify PSI alerting works correctly | 3 | P1 |
| E8-S7 | As QA, edge case tests cover null inputs, boundary values, max load | 5 | P2 |

---

## 🏃 Sprint Plans

### SPRINT 1: Foundation (2024-01-08 → 2024-01-19) — 40pts
**Theme:** Platform foundation + security baseline

| Story | Pts | Owner | Status |
|-------|-----|-------|--------|
| E2-S1: FastAPI app setup | 3 | Backend | ✅ Done |
| E2-S2: JWT + Azure AD RBAC | 8 | Backend | ✅ Done |
| E2-S3: PII masking middleware | 8 | Backend | ✅ Done |
| E6-S4: Secrets in Key Vault | 3 | Security | ✅ Done |
| E7-S1: docker-compose setup | 3 | DevOps | ✅ Done |
| E3-S3: Azure SQL schema | 5 | Data | ✅ Done |
| E1-S1: Databricks EDA | 5 | ML | ✅ Done |
| E7-S2: CI pipeline | 5 | DevOps | ✅ Done |

**Sprint Velocity:** 40pts ✅

---

### SPRINT 2: Core ML (2024-01-22 → 2024-02-02) — 39pts
**Theme:** Feature engineering + churn model

| Story | Pts | Owner | Status |
|-------|-----|-------|--------|
| E1-S2: Feature engineering pipeline | 8 | ML | ✅ Done |
| E1-S3: Churn model training | 13 | ML | ✅ Done |
| E1-S4: MLflow model registry | 5 | ML | ✅ Done |
| E2-S4: Audit logging | 5 | Backend | ✅ Done |
| E3-S1: Bronze/Silver/Gold ingestion | 8 | Data | ✅ Done |

**Sprint Velocity:** 39pts ✅

---

### SPRINT 3: APIs + GDPR (2024-02-05 → 2024-02-16) — 39pts
**Theme:** Core API endpoints + GDPR compliance

| Story | Pts | Owner | Status |
|-------|-----|-------|--------|
| E2-S5: Churn prediction API | 8 | Backend | ✅ Done |
| E2-S10: GDPR erasure endpoint | 8 | Backend | ✅ Done |
| E2-S11: Consent + data export | 5 | Backend | ✅ Done |
| E6-S1: Art.17 erasure workflow | 8 | Security | ✅ Done |
| E6-S2: Art.15 access export | 5 | Security | ✅ Done |
| E6-S3: Consent management | 5 | Backend | ✅ Done |

**Sprint Velocity:** 39pts ✅

---

### SPRINT 4: Segmentation + Anomaly (2024-02-19 → 2024-03-01) — 40pts
**Theme:** Segmentation model + anomaly detection

| Story | Pts | Owner | Status |
|-------|-----|-------|--------|
| E1-S5: Segmentation model | 8 | ML | ✅ Done |
| E1-S6: Anomaly detection model | 8 | ML | ✅ Done |
| E2-S6: Segmentation API | 5 | Backend | ✅ Done |
| E2-S7: Anomaly detection API | 8 | Backend | ✅ Done |
| E3-S2: Ingestion PII masking | 8 | Data | ✅ Done |
| E8-S1: API unit tests | 3 | QA | ✅ Done |

**Sprint Velocity:** 40pts ✅

---

### SPRINT 5: GenAI + Retention (2024-03-04 → 2024-03-15) — 42pts
**Theme:** GenAI explanations + retention engine

| Story | Pts | Owner | Status |
|-------|-----|-------|--------|
| E4-S4: RAG with Cognitive Search | 13 | ML | ✅ Done |
| E4-S1: ChurnExplanation GenAI | 8 | ML | ✅ Done |
| E4-S2: Retention action plan GenAI | 8 | ML | ✅ Done |
| E2-S8: Retention recommendations API | 8 | Backend | ✅ Done |
| E2-S9: GenAI insights API | 5 | Backend | ✅ Done |

**Sprint Velocity:** 42pts ✅

---

### SPRINT 6: Power BI Dashboards (2024-03-18 → 2024-03-29) — 38pts
**Theme:** Executive dashboards

| Story | Pts | Owner | Status |
|-------|-----|-------|--------|
| E5-S1: Churn rate trend dashboard | 5 | BI | ✅ Done |
| E5-S2: High-risk customer heatmap | 5 | BI | ✅ Done |
| E5-S5: Revenue-at-risk dashboard | 8 | BI | ✅ Done |
| E5-S3: Customer segments dashboard | 5 | BI | ✅ Done |
| E5-S4: Anomaly trends dashboard | 5 | BI | ✅ Done |
| E5-S6: Model health dashboard | 5 | BI | ✅ Done |
| E1-S7: Fairness audit | 5 | ML | ✅ Done |

**Sprint Velocity:** 38pts ✅

---

### SPRINT 7: Testing + Security (2024-04-01 → 2024-04-12) — 41pts
**Theme:** Full QA pass + security hardening

| Story | Pts | Owner | Status |
|-------|-----|-------|--------|
| E8-S2: ML accuracy tests | 5 | QA | ✅ Done |
| E8-S3: GDPR compliance tests | 5 | QA | ✅ Done |
| E8-S4: Security tests | 5 | QA | ✅ Done |
| E8-S5: Bias/fairness tests | 5 | QA | ✅ Done |
| E6-S5: SAST/DAST CI scans | 5 | Security | ✅ Done |
| E6-S6: Immutable audit log tests | 5 | Security | ✅ Done |
| E1-S8: Drift detection | 5 | ML | ✅ Done |
| E8-S6: Drift alert tests | 3 | QA | ✅ Done |
| E3-S4: Retention policy automation | 3 | Data | ✅ Done |

**Sprint Velocity:** 41pts ✅

---

### SPRINT 8: Deployment + Release (2024-04-14 → 2024-04-25) — 38pts
**Theme:** Production deployment + final hardening

| Story | Pts | Owner | Status |
|-------|-----|-------|--------|
| E7-S3: CD staging deployment | 5 | DevOps | ✅ Done |
| E7-S4: CD production deployment | 5 | DevOps | ✅ Done |
| E7-S5: Azure Bicep IaC | 8 | DevOps | ✅ Done |
| E2-S12: Batch prediction endpoint | 5 | Backend | ✅ Done |
| E4-S3: Executive risk narratives | 5 | ML | ✅ Done |
| E5-S7: Retention campaign ROI | 5 | BI | ✅ Done |
| E8-S7: Edge case tests | 5 | QA | ✅ Done |

**Sprint Velocity:** 38pts ✅

---

## 📊 Velocity Chart

```
Sprint  │ Committed │ Delivered │ Trend
────────┼───────────┼───────────┼──────
Sprint 1│    40     │    40     │ ──
Sprint 2│    40     │    39     │ ▼1
Sprint 3│    40     │    39     │ ──
Sprint 4│    40     │    40     │ ▲1
Sprint 5│    40     │    42     │ ▲2
Sprint 6│    40     │    38     │ ▼4
Sprint 7│    40     │    41     │ ▲3
Sprint 8│    40     │    38     │ ▼3
────────┼───────────┼───────────┼──────
Total   │   320     │   317     │ 99.1%
```

**Average Velocity:** 39.6 pts/sprint  
**Predictability:** 99.1%

---

## 🐛 Bug/Risk Backlog

| ID | Issue | Severity | Sprint Target |
|----|-------|----------|---------------|
| BUG-01 | Class imbalance in churn labels (2:1 ratio) → addressed with SMOTE | P1 | Sprint 2 |
| BUG-02 | Redis cache TTL too long causing stale predictions | P2 | Sprint 4 |
| BUG-03 | SHAP values slow for large batches (>1000 customers) | P2 | Sprint 5 |
| RISK-01 | Azure OpenAI rate limits in prod peak hours | P1 | Sprint 5 |
| RISK-02 | GDPR deletion cascade misses Cosmos DB events | P0 | Sprint 3 |
| RISK-03 | Model drift not detected fast enough (daily job too slow) | P1 | Sprint 7 |

---

## 📈 Release Milestones

| Milestone | Date | Contents |
|-----------|------|---------|
| **Alpha** (internal) | 2024-02-16 | Core APIs + churn model |
| **Beta** (limited pilot) | 2024-03-15 | All models + GenAI |
| **RC1** (UAT) | 2024-04-12 | Full platform, security-tested |
| **v1.0.0** (production) | 2024-04-25 | GA release |
| **v1.1.0** (streaming) | 2024-06-28 | Real-time features + Delta Live Tables |

---

## 👥 Team Capacity

| Team Member | Role | FTE | Sprints |
|-------------|------|-----|---------|
| Lead Architect | AI/Data Architect | 0.5 | All |
| ML Engineer A | Model training, MLflow | 1.0 | All |
| ML Engineer B | GenAI, RAG, features | 1.0 | S5-S8 |
| Backend Engineer | FastAPI, Azure integration | 1.0 | All |
| Data Engineer | Databricks, pipelines | 1.0 | All |
| Security/GDPR | RBAC, audit, GDPR | 0.5 | All |
| BI Developer | Power BI, DAX | 1.0 | S6-S8 |
| QA Engineer | Testing, automation | 1.0 | S4-S8 |
