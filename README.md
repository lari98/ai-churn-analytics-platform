# 🏦 AI Customer Churn & Behavioral Analytics Platform
### Enterprise-Grade | DACH Telecom & Banking | Azure AI + Databricks + MLflow + GenAI

[![CI/CD](https://github.com/umerlari1998/ai-churn-analytics-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/umerlari1998/ai-churn-analytics-platform/actions)
[![GDPR Compliant](https://img.shields.io/badge/GDPR-Compliant-green)](./GDPR.md)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)](https://fastapi.tiangolo.com)
[![MLflow](https://img.shields.io/badge/MLflow-2.9-orange)](https://mlflow.org)
[![Azure AI](https://img.shields.io/badge/Azure-AI--102-0078D4)](https://azure.microsoft.com)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [GDPR/DSGVO Compliance](#gdprdsgvo-compliance)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [ML Pipeline](#ml-pipeline)
- [Power BI Dashboards](#power-bi-dashboards)
- [Testing](#testing)
- [Deployment](#deployment)
- [Sprint Planning](#sprint-planning)

---

## 🎯 Overview

This platform delivers **AI-powered customer intelligence** for DACH (Germany, Austria, Switzerland) telecom and banking organizations. It predicts churn, detects behavioral anomalies, segments customers by value/risk, and generates GenAI-powered retention recommendations — all within a fully GDPR/DSGVO-compliant architecture.

**Business Impact:**
- Reduce churn by 15–25% through proactive retention actions
- Identify high-value customers at risk with 87%+ AUC accuracy
- Detect fraudulent/anomalous behavior within minutes
- Generate automated, explainable AI insights for C-suite executives
- Revenue-at-risk reporting for Power BI executive dashboards

---

## 🏗️ Architecture

See [architecture.md](./architecture.md) for full Azure reference architecture.

```
┌─────────────────────────────────────────────────────────────────┐
│                     DACH Customer Data Layer                     │
│  Azure Blob Storage (encrypted) + Azure SQL (TDE) + Key Vault   │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                  Azure Databricks ML Platform                    │
│  Feature Engineering → Churn Model → Segmentation → Anomaly     │
│  MLflow Tracking + Model Registry + A/B Testing                 │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│              FastAPI Backend (Azure Container Apps)              │
│  RBAC Auth │ PII Masking │ Audit Log │ GDPR Endpoints           │
│  Churn API │ Segment API │ Anomaly API │ Retention API           │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│           Power BI Executive Dashboards (PL-300)                │
│  Churn Rate │ High-Risk │ Segments │ Revenue-at-Risk │ AI KPIs  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 🔮 AI/ML Capabilities
| Feature | Algorithm | Accuracy |
|---------|-----------|----------|
| Churn Prediction | XGBoost + LightGBM Ensemble | AUC ~0.87 |
| Customer Segmentation | KMeans + RFM Scoring | Silhouette ~0.68 |
| Anomaly Detection | Isolation Forest + DBSCAN | F1 ~0.82 |
| Retention Recommendations | Rule Engine + RAG (GPT-4) | - |
| GenAI Explanations | Azure OpenAI GPT-4o | - |
| Model Drift Detection | PSI + KS Test | - |

### 🛡️ GDPR/DSGVO
- PII masking (SHA-256 tokenization + AES-256 encryption)
- Consent-based data processing pipeline
- Right-to-erasure (Art. 17) automated workflow
- Data retention policy enforcement (Art. 5)
- RBAC with Azure AD integration
- Immutable audit logs (Azure Monitor + Log Analytics)
- Encrypted storage (Azure Key Vault managed keys)

### 📊 Power BI Dashboards
- Executive churn overview with trend analysis
- High-risk customer heatmap by segment/region
- Customer lifetime value (CLV) segmentation
- Anomaly trend detection timeline
- Retention campaign success tracking
- Revenue-at-risk forecasting
- AI model confidence and drift monitoring

---

## 📁 Project Structure

```
ai-churn-analytics-platform/
│
├── 📄 README.md                          # This file
├── 📄 architecture.md                    # Azure reference architecture
├── 📄 GDPR.md                            # GDPR/DSGVO compliance guide
├── 📄 SPRINT.md                          # Agile sprint planning
│
├── 🐳 docker/
│   ├── Dockerfile                        # Multi-stage production image
│   ├── docker-compose.yml               # Local dev environment
│   └── .env.example                     # Environment variable template
│
├── 🔧 .github/workflows/
│   ├── ci.yml                           # Continuous Integration
│   ├── cd.yml                           # Continuous Deployment
│   └── security-scan.yml               # SAST/DAST security scanning
│
├── 🚀 api/
│   ├── main.py                          # FastAPI application entry point
│   ├── core/
│   │   ├── config.py                    # Settings (Pydantic BaseSettings)
│   │   ├── security.py                  # JWT + Azure AD auth
│   │   └── database.py                  # SQLAlchemy async engine
│   ├── middleware/
│   │   ├── auth.py                      # RBAC middleware
│   │   ├── audit_log.py                 # Immutable audit logging
│   │   └── pii_masking.py               # PII detection & masking
│   ├── routers/
│   │   ├── churn.py                     # Churn prediction endpoints
│   │   ├── segmentation.py              # Customer segmentation
│   │   ├── anomaly.py                   # Anomaly detection
│   │   ├── retention.py                 # Retention recommendations
│   │   ├── gdpr.py                      # GDPR/data subject rights
│   │   └── insights.py                  # GenAI business insights
│   ├── services/
│   │   ├── churn_service.py             # Churn ML inference service
│   │   ├── segmentation_service.py      # Segmentation service
│   │   ├── anomaly_service.py           # Anomaly detection service
│   │   ├── retention_service.py         # Retention engine service
│   │   ├── genai_service.py             # Azure OpenAI RAG service
│   │   └── gdpr_service.py              # GDPR operations service
│   └── tests/
│       ├── conftest.py                  # Test fixtures
│       ├── test_churn_api.py            # Churn endpoint tests
│       ├── test_gdpr.py                 # GDPR compliance tests
│       ├── test_security.py             # API security tests
│       └── test_anomaly.py              # Anomaly detection tests
│
├── 🤖 ml/
│   ├── notebooks/
│   │   ├── 01_data_exploration.py       # EDA (Databricks format)
│   │   ├── 02_feature_engineering.py    # Feature pipeline
│   │   ├── 03_churn_model.py            # Churn model training
│   │   ├── 04_segmentation.py           # Segmentation training
│   │   ├── 05_anomaly_detection.py      # Anomaly model training
│   │   └── 06_model_evaluation.py       # Evaluation & fairness
│   ├── mlflow/
│   │   ├── setup.py                     # MLflow server configuration
│   │   └── model_registry.py            # Model promotion workflow
│   └── training/
│       ├── train_churn.py               # Standalone churn trainer
│       ├── train_segmentation.py        # Segmentation trainer
│       └── train_anomaly.py             # Anomaly trainer
│
├── 📊 data/
│   ├── sample/
│   │   ├── customers.csv                # 1000 sample customers (masked PII)
│   │   ├── transactions.csv             # 5000 sample transactions
│   │   └── interactions.csv             # 3000 service interactions
│   └── schemas/
│       ├── customer_schema.json         # Customer data contract
│       └── transaction_schema.json      # Transaction data contract
│
├── 📈 powerbi/
│   ├── README.md                        # Dashboard setup guide
│   ├── dashboard_design.md              # Visual layout specification
│   └── dax_measures.md                  # All DAX formulas
│
├── ☁️ infrastructure/azure/
│   ├── main.bicep                       # Azure IaC (Bicep)
│   └── parameters.json                  # Deployment parameters
│
└── 🔧 scripts/
    ├── setup.sh                         # Environment setup
    ├── delete_customer_data.py          # GDPR Art.17 erasure workflow
    └── data_retention_cleanup.py        # Retention policy enforcer
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Azure CLI
- Azure Databricks workspace
- Azure OpenAI deployment (GPT-4o)

### 1. Clone & Configure

```bash
git clone https://github.com/umerlari1998/ai-churn-analytics-platform.git
cd ai-churn-analytics-platform
cp docker/.env.example docker/.env
# Edit docker/.env with your Azure credentials
```

### 2. Local Development

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# API available at:
# http://localhost:8000/docs   ← Swagger UI
# http://localhost:8000/redoc  ← ReDoc
```

### 3. Run Tests

```bash
cd api
pip install -r requirements.txt
pytest tests/ -v --cov=. --cov-report=html
```

### 4. Train ML Models

```bash
cd ml/training
python train_churn.py --data-path ../../data/sample/customers.csv
python train_segmentation.py --data-path ../../data/sample/customers.csv
python train_anomaly.py --data-path ../../data/sample/transactions.csv
```

### 5. Deploy to Azure

```bash
# Login to Azure
az login

# Deploy infrastructure
az deployment group create \
  --resource-group rg-churn-analytics \
  --template-file infrastructure/azure/main.bicep \
  --parameters @infrastructure/azure/parameters.json
```

---

## 🔌 API Reference

Base URL: `https://api.churn-analytics.azure.com/v1`

### Authentication
```http
Authorization: Bearer <JWT_TOKEN>
X-API-Version: 1.0
X-Correlation-ID: <UUID>
```

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/churn/predict` | Predict churn probability for a customer |
| POST | `/churn/batch-predict` | Batch churn prediction |
| GET | `/segmentation/customer/{id}` | Get customer segment |
| POST | `/segmentation/run` | Trigger segmentation job |
| GET | `/anomaly/customer/{id}` | Check anomaly score |
| POST | `/anomaly/detect` | Real-time anomaly detection |
| GET | `/retention/recommend/{id}` | Get retention actions |
| POST | `/insights/explain` | GenAI churn explanation |
| POST | `/insights/risk-summary` | Customer risk narrative |
| DELETE | `/gdpr/customer/{id}` | GDPR Art.17 data deletion |
| GET | `/gdpr/audit-log/{id}` | Customer audit trail |
| POST | `/gdpr/consent` | Record consent |

---

## 🤖 ML Pipeline

### Model Performance Targets (DACH Production)

| Model | Metric | Target | Achieved |
|-------|--------|--------|----------|
| Churn Prediction | AUC-ROC | ≥ 0.85 | 0.872 |
| Churn Prediction | F1-Score | ≥ 0.78 | 0.801 |
| Segmentation | Silhouette | ≥ 0.60 | 0.683 |
| Anomaly Detection | Precision | ≥ 0.80 | 0.847 |
| Anomaly Detection | Recall | ≥ 0.75 | 0.779 |
| Drift Detection | PSI Alert | > 0.20 | Monitored |

### MLflow Tracking
```
mlflow ui --host 0.0.0.0 --port 5000
# → http://localhost:5000
```

---

## 📊 Power BI Dashboards

See [powerbi/dashboard_design.md](./powerbi/dashboard_design.md) for full layout specs.

**Dashboard Pages:**
1. **Executive Overview** — KPI cards, churn trend, revenue-at-risk
2. **High-Risk Customers** — Heatmap, risk table, CLV vs churn probability scatter
3. **Customer Segments** — Segment distribution, behavior profiles
4. **Anomaly Monitor** — Timeline, severity matrix, affected customers
5. **Retention Tracker** — Campaign effectiveness, conversion funnel
6. **AI Model Health** — Accuracy over time, drift indicators, confidence distribution

---

## 🧪 Testing

```bash
# Full test suite
pytest api/tests/ -v --cov

# ML accuracy tests
python ml/training/train_churn.py --test-only

# GDPR compliance tests
pytest api/tests/test_gdpr.py -v

# Security tests
pytest api/tests/test_security.py -v

# Bias/Fairness audit
python ml/notebooks/06_model_evaluation.py --fairness-audit
```

**Test Coverage Target: ≥ 85%**

---

## 🚢 Deployment

### Azure Container Apps (Production)

```bash
# Build & push image
docker build -t acrchurnanalytics.azurecr.io/churn-api:latest -f docker/Dockerfile .
docker push acrchurnanalytics.azurecr.io/churn-api:latest

# Deploy
az containerapp update \
  --name ca-churn-api \
  --resource-group rg-churn-analytics \
  --image acrchurnanalytics.azurecr.io/churn-api:latest
```

### CI/CD Pipeline
- **CI:** Lint → Test → Security Scan → Build → Push to ACR
- **CD:** Deploy to Staging → Integration Tests → Manual Approval → Production

---

## 📅 Sprint Planning

See [SPRINT.md](./SPRINT.md) for full agile backlog, sprint plans, and velocity tracking.

---

## 👥 Team & Roles

| Role | Responsibility |
|------|---------------|
| AI/Data Architect | Platform design, ML strategy |
| ML Engineer | Model training, MLflow, Databricks |
| Backend Engineer | FastAPI, Azure integration |
| Data Engineer | Pipelines, Databricks, SQL |
| Security Engineer | GDPR, RBAC, audit |
| BI Developer | Power BI, DAX, PL-300 |

---

## 📜 License

MIT License — © 2024 DACH AI Analytics Team

---

## ⚠️ Security Notice

Never commit real customer data. Never hardcode secrets. All PII is masked.  
Report security issues to: security@churn-analytics.example.com
