# 🏗️ Azure Reference Architecture
## AI Customer Churn & Behavioral Analytics Platform — DACH Edition

**Version:** 1.0.0  
**Standard:** Azure Well-Architected Framework  
**Certification Alignment:** AI-102, PL-300, DP-203

---

## 1. Architecture Overview

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DACH CUSTOMER DATA SOURCES                                ║
║  CRM Systems │ Call Center │ Mobile App │ Web Portal │ Payment Gateway       ║
╚══════════════════════╦═══════════════════════════════════════════════════════╝
                       ║ (TLS 1.3 encrypted ingestion)
╔══════════════════════▼═══════════════════════════════════════════════════════╗
║                    INGESTION & LANDING ZONE                                  ║
║  Azure Event Hubs (real-time)  │  Azure Data Factory (batch)                 ║
║  Azure Service Bus (queuing)   │  Azure API Management (gateway)             ║
╚══════════════════════╦═══════════════════════════════════════════════════════╝
                       ║
╔══════════════════════▼═══════════════════════════════════════════════════════╗
║                    RAW DATA LAKE (BRONZE LAYER)                              ║
║  Azure Data Lake Storage Gen2 (ADLS)                                        ║
║  ├── /raw/customers/          (PII encrypted, AES-256)                       ║
║  ├── /raw/transactions/       (partitioned by date)                          ║
║  └── /raw/interactions/       (event logs)                                   ║
║  Security: Azure Key Vault CMK │ RBAC │ Private Endpoint                    ║
╚══════════════════════╦═══════════════════════════════════════════════════════╝
                       ║ (Databricks Delta Lake ETL)
╔══════════════════════▼═══════════════════════════════════════════════════════╗
║                PROCESSED DATA LAKE (SILVER + GOLD LAYERS)                   ║
║  Azure Databricks (Premium Tier)                                             ║
║  ├── Silver: Cleansed, PII-masked, validated data                            ║
║  ├── Gold:   Feature-engineered, ML-ready datasets                           ║
║  └── Delta Live Tables: Streaming feature computation                        ║
╚══════════════════════╦═══════════════════════════════════════════════════════╝
                       ║
╔══════════════════════▼═══════════════════════════════════════════════════════╗
║                    ML TRAINING PLATFORM                                      ║
║  Azure Databricks ML                                                         ║
║  ├── Churn Prediction:    XGBoost + LightGBM Ensemble                        ║
║  ├── Segmentation:        KMeans + RFM Scoring + UMAP                        ║
║  ├── Anomaly Detection:   Isolation Forest + DBSCAN                          ║
║  └── Retention Engine:    Rule-based + RAG recommendations                   ║
║                                                                              ║
║  MLflow Tracking (Azure ML backend)                                          ║
║  ├── Experiment tracking  │  Model versioning                                ║
║  ├── Model Registry       │  A/B test management                             ║
║  └── Drift monitoring     │  Performance dashboards                          ║
╚══════════════════════╦═══════════════════════════════════════════════════════╝
                       ║ (Model serving via Azure ML Online Endpoints)
╔══════════════════════▼═══════════════════════════════════════════════════════╗
║                    SERVING LAYER                                             ║
║  FastAPI Backend (Azure Container Apps)                                      ║
║  ├── Churn Prediction API     (real-time + batch)                            ║
║  ├── Segmentation API         (customer segments)                            ║
║  ├── Anomaly Detection API    (real-time scoring)                            ║
║  ├── Retention Recommendation (GenAI + rules)                                ║
║  ├── GDPR Compliance API      (data subject rights)                          ║
║  └── GenAI Insights API       (Azure OpenAI GPT-4o)                         ║
║                                                                              ║
║  Cross-cutting:                                                              ║
║  ├── Azure AD B2C → JWT Auth + RBAC                                          ║
║  ├── Azure API Management → Rate limiting, versioning                        ║
║  ├── Azure Monitor + Log Analytics → Audit trail                             ║
║  └── Azure Key Vault → Secrets, certificates                                 ║
╚══════════════════════╦═══════════════════════════════════════════════════════╝
                       ║
╔══════════════════════▼═══════════════════════════════════════════════════════╗
║                PERSISTENCE LAYER                                             ║
║  Azure SQL Database (Business Tier)                                          ║
║  ├── Customer profiles (masked)                                              ║
║  ├── Churn scores + history                                                  ║
║  ├── Segmentation results                                                    ║
║  ├── Audit logs (immutable)                                                  ║
║  └── GDPR consent records                                                    ║
║                                                                              ║
║  Azure Cosmos DB (NoSQL)                                                     ║
║  └── Real-time anomaly events                                                ║
║                                                                              ║
║  Azure Cache for Redis                                                       ║
║  └── Model prediction cache (TTL: 1h)                                       ║
╚══════════════════════╦═══════════════════════════════════════════════════════╝
                       ║
╔══════════════════════▼═══════════════════════════════════════════════════════╗
║              VISUALIZATION & REPORTING LAYER                                 ║
║  Power BI Premium (PL-300 compliant)                                         ║
║  ├── Executive Dashboard:     Churn rate, revenue-at-risk                    ║
║  ├── Risk Dashboard:          High-risk heatmap, CLV scatter                 ║
║  ├── Segment Dashboard:       Customer profiles, RFM matrix                  ║
║  ├── Anomaly Dashboard:       Timeline, severity, affected count             ║
║  ├── Retention Dashboard:     Campaign ROI, funnel conversion                ║
║  └── Model Health Dashboard:  AUC trend, drift alerts, confidence            ║
║                                                                              ║
║  Data Sources: Direct Query → Azure SQL │ Import → ADLS parquet              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Component Detail

### 2.1 Data Ingestion

| Component | Azure Service | Purpose |
|-----------|---------------|---------|
| Real-time events | Azure Event Hubs | Customer behavior stream |
| Batch loads | Azure Data Factory | Nightly CRM sync |
| API gateway | Azure API Management | Rate limiting, auth |
| Message queue | Azure Service Bus | Async processing |

### 2.2 Storage Architecture (Medallion)

```
BRONZE (Raw)          SILVER (Clean)         GOLD (ML-Ready)
────────────         ──────────────          ──────────────
Raw ingested    →    PII masked         →    Feature-engineered
JSON/CSV/Parquet     Validated/typed         RFM features
Immutable            Deduped                 Churn labels
7-year retention     GDPR tagged             Train/test splits
```

### 2.3 Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  SECURITY PERIMETER                      │
│                                                          │
│  Azure AD (Identity)    Azure Key Vault (Secrets)        │
│  ├── Service Principals  ├── DB connection strings       │
│  ├── Managed Identities  ├── API keys (OpenAI, etc.)     │
│  └── RBAC roles          ├── Encryption keys (CMK)       │
│                          └── TLS certificates            │
│                                                          │
│  Network:                                                │
│  ├── Azure Private Link (all PaaS services)              │
│  ├── Azure Virtual Network (isolated subnets)            │
│  ├── Network Security Groups (layer-4 firewall)          │
│  └── Azure Firewall (layer-7, egress filtering)          │
│                                                          │
│  Data Protection:                                        │
│  ├── TDE (Transparent Data Encryption) on Azure SQL      │
│  ├── AES-256 on ADLS (CMK via Key Vault)                 │
│  ├── PII tokenization (SHA-256 + HMAC)                   │
│  └── In-transit: TLS 1.3 minimum                        │
└─────────────────────────────────────────────────────────┘
```

### 2.4 ML Architecture (AI-102 Aligned)

```
DATA PREPARATION
├── Azure Databricks: PySpark feature pipeline
├── Delta Live Tables: streaming features
└── Feature Store: versioned, reusable features

MODEL TRAINING
├── Experiment: MLflow tracking (params, metrics, artifacts)
├── Churn Model: XGBoost base + LightGBM + Logistic (ensemble)
├── Hyperparameter Tuning: Hyperopt (Bayesian)
└── Cross-validation: Stratified 5-fold (class imbalance aware)

MODEL EVALUATION
├── Metrics: AUC, F1, Precision, Recall, Brier Score
├── Fairness: Disparate impact across age/gender groups
├── Explainability: SHAP values per prediction
└── Drift: PSI (Population Stability Index) ≥ 0.20 → retrain

MODEL DEPLOYMENT
├── Azure ML Online Endpoint (real-time, <100ms p95)
├── Azure ML Batch Endpoint (nightly scoring)
├── Blue/Green deployment (zero downtime)
└── Canary rollout (10% → 50% → 100% traffic)

MODEL MONITORING
├── Azure Monitor: inference latency, error rate
├── Application Insights: prediction distribution
├── MLflow: model performance over time
└── Automated retraining trigger (drift detected)
```

### 2.5 GenAI / RAG Architecture

```
USER REQUEST → FastAPI
     │
     ▼
CONTEXT RETRIEVAL (RAG)
├── Azure Cognitive Search (vector index)
│   ├── Customer profile embeddings
│   ├── Historical churn patterns
│   └── Retention playbook embeddings
└── Azure SQL: current customer data

     │
     ▼
PROMPT ENGINEERING
├── System: "You are a DACH banking/telecom retention expert..."
├── Context: retrieved customer facts
├── Instruction: generate retention recommendation
└── GDPR constraint: "Never mention full names or account numbers"

     │
     ▼
AZURE OPENAI (GPT-4o)
└── Temperature: 0.2 (deterministic business output)

     │
     ▼
RESPONSE VALIDATION
├── PII scanner (redact leaked PII)
├── Hallucination check (grounding score)
└── Structured JSON output (validated with Pydantic)
```

---

## 3. RBAC Roles

| Role | Access | Example |
|------|--------|---------|
| `platform-admin` | Full admin | Platform team |
| `ml-engineer` | ML + data read/write | Databricks team |
| `api-consumer` | API read only | CRM integration |
| `bi-analyst` | Power BI + aggregated data | BI team |
| `gdpr-officer` | GDPR endpoints only | DPO |
| `auditor` | Audit logs read-only | Compliance |

---

## 4. Disaster Recovery

| Component | RTO | RPO | Strategy |
|-----------|-----|-----|----------|
| Azure SQL | 4h | 1h | Geo-replication (paired region) |
| ADLS | 2h | 15m | RA-GRS (read-access geo-redundant) |
| Container Apps | 30m | 0 | Multi-region deployment |
| MLflow models | 8h | 24h | ACR geo-replication |

**Paired Region:** West Europe ↔ North Europe (GDPR data residency maintained)

---

## 5. Cost Estimation (Monthly, EUR)

| Component | Tier | Est. Cost |
|-----------|------|-----------|
| Azure Databricks | Premium DBU | €2,400 |
| Azure SQL | Business Critical | €800 |
| Azure Container Apps | Standard | €300 |
| Azure OpenAI | GPT-4o | €500 |
| Azure Storage (ADLS) | LRS | €150 |
| Azure Monitor / Sentinel | Standard | €400 |
| Power BI Premium | P1 | €4,200 |
| **Total** | | **~€8,750/mo** |

---

## 6. Compliance Certifications

- ✅ GDPR / DSGVO (EU Regulation 2016/679)
- ✅ BSI IT-Grundschutz (German federal security standard)
- ✅ ISO 27001 (Azure inherited)
- ✅ SOC 2 Type II (Azure inherited)
- ✅ BaFin AI Guidelines (German banking regulator)
- ✅ Swiss FINMA data governance requirements
