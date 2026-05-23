# Databricks notebook source
# MAGIC %md
# MAGIC # 06 — Model Evaluation, Fairness Audit & Drift Detection
# MAGIC ## QA gate for production model promotion

# COMMAND ----------
import mlflow, shap, numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, f1_score, classification_report
from sklearn.model_selection import train_test_split

# COMMAND ----------
# MAGIC %md ## Load Production Model & Test Data

# COMMAND ----------
mlflow.set_tracking_uri("azureml://westeurope.api.azureml.ms/mlflow/v1.0/subscriptions/...")
model = mlflow.sklearn.load_model("models:/churn-prediction-ensemble/Staging")

df = spark.table("gold.customer_churn_features_v2").toPandas()
FEATURES = ["tenure_months","monthly_charge_eur","total_charges_eur","num_products",
            "support_tickets_6m","payment_delay_count_12m","avg_monthly_usage_gb",
            "days_since_last_contact","nps_score","contract_type_encoded",
            "payment_method_encoded","has_internet_service","has_phone_service",
            "charge_per_month","ticket_rate","product_engagement","tenure_bucket"]
available = [f for f in FEATURES if f in df.columns]
X = df[available].fillna(0)
y = df["churned"].astype(int)
_, X_test, _, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# COMMAND ----------
# MAGIC %md ## Core Metrics

# COMMAND ----------
y_proba = model.predict_proba(X_test)[:,1]
y_pred  = (y_proba >= 0.5).astype(int)
auc = roc_auc_score(y_test, y_proba)
f1  = f1_score(y_test, y_pred)
print(f"AUC-ROC: {auc:.4f}  F1: {f1:.4f}")
print(classification_report(y_test, y_pred))
assert auc >= 0.85, f"❌ QA GATE FAILED: AUC {auc:.4f} < 0.85"
assert f1  >= 0.78, f"❌ QA GATE FAILED: F1  {f1:.4f} < 0.78"
print("✅ QA gates passed")

# COMMAND ----------
# MAGIC %md ## Fairness Audit (GDPR / AI Act)

# COMMAND ----------
if "age_bucket" in df.columns:
    idx = X_test.index
    for grp in df.loc[idx, "age_bucket"].unique():
        mask = df.loc[idx, "age_bucket"] == grp
        if mask.sum() < 30: continue
        grp_auc = roc_auc_score(y_test[mask.values], y_proba[mask.values])
        delta = abs(grp_auc - auc)
        status = "✅" if delta < 0.05 else "⚠️"
        print(f"  {status} age_bucket={grp}: AUC={grp_auc:.4f}  Δ={delta:.4f}")

# COMMAND ----------
# MAGIC %md ## PSI Drift Detection

# COMMAND ----------
def psi(expected, actual, bins=10):
    bp = np.percentile(expected, np.linspace(0,100,bins+1))
    bp[0]=-np.inf; bp[-1]=np.inf
    e = np.histogram(expected, bp)[0]/len(expected)+1e-10
    a = np.histogram(actual,   bp)[0]/len(actual)+1e-10
    return float(np.sum((e-a)*np.log(e/a)))

# Compare current vs prior month predictions
prior_proba = spark.table("gold.churn_scores").filter("scored_at < date_sub(current_date(),30)").toPandas()["churn_probability"].values if True else y_proba
p = psi(prior_proba, y_proba)
print(f"PSI: {p:.4f} — {'✅ Stable' if p < 0.10 else '⚠️ Slight drift' if p < 0.20 else '❌ Retrain required'}")
mlflow.log_metric("psi_score", p)

# COMMAND ----------
# MAGIC %md ## Promote if all gates pass

# COMMAND ----------
from mlflow.tracking import MlflowClient
client = MlflowClient()
versions = client.get_latest_versions("churn-prediction-ensemble", stages=["Staging"])
if versions:
    v = versions[0].version
    client.transition_model_version_stage("churn-prediction-ensemble", v, "Production", archive_existing_versions=True)
    print(f"✅ Model v{v} promoted to Production")
