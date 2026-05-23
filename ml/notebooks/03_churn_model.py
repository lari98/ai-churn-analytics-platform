# Databricks notebook source
# MAGIC %md
# MAGIC # Churn Prediction Model — Databricks ML
# MAGIC ## AI Customer Churn & Behavioral Analytics Platform
# MAGIC ### Version: 1.0 | Environment: Azure Databricks Premium | Runtime: 14.3 ML

# COMMAND ----------
# MAGIC %md ## 1. Setup & Imports

# COMMAND ----------

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import shap
from databricks.feature_store import FeatureStoreClient
from imblearn.over_sampling import SMOTE
from lightgbm import LGBMClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.model_selection import train_test_split, StratifiedKFold
from xgboost import XGBClassifier

# Configure MLflow to use Azure ML backend
mlflow.set_tracking_uri("azureml://westeurope.api.azureml.ms/mlflow/v1.0/subscriptions/...")
mlflow.set_experiment("/Users/ml-team@company.com/churn-prediction")

print("✅ Imports complete")

# COMMAND ----------
# MAGIC %md ## 2. Load Data from Feature Store

# COMMAND ----------

fs = FeatureStoreClient()

# Load from Gold layer (anonymised features, no PII)
customer_features_df = spark.table("gold.customer_churn_features")
print(f"Loaded {customer_features_df.count():,} customers from Feature Store")
display(customer_features_df.limit(5))

# COMMAND ----------
# MAGIC %md ## 3. Exploratory Analysis

# COMMAND ----------

import matplotlib.pyplot as plt

# Churn distribution
churn_rate = customer_features_df.agg({"churned": "mean"}).collect()[0][0]
print(f"Overall churn rate: {churn_rate:.2%}")

# Class imbalance check
churn_counts = customer_features_df.groupBy("churned").count()
display(churn_counts)

# Feature correlation
df_pandas = customer_features_df.toPandas()
corr = df_pandas.corr()["churned"].sort_values(ascending=False)
print("\nTop correlations with churn:")
print(corr.head(10))

# COMMAND ----------
# MAGIC %md ## 4. Feature Engineering

# COMMAND ----------

from pyspark.sql import functions as F

enriched_df = customer_features_df.withColumns({
    "charge_per_month": F.col("total_charges_eur") / (F.col("tenure_months") + 1),
    "ticket_rate": F.col("support_tickets_6m") / (F.col("tenure_months") + 1) * 6,
    "product_engagement": F.col("num_products") * F.col("avg_monthly_usage_gb"),
    "tenure_bucket": F.when(F.col("tenure_months") <= 6, 0)
                      .when(F.col("tenure_months") <= 12, 1)
                      .when(F.col("tenure_months") <= 24, 2)
                      .when(F.col("tenure_months") <= 48, 3)
                      .otherwise(4),
})
display(enriched_df.limit(3))

# Write engineered features back to Feature Store
fs.write_table(
    name="gold.customer_churn_features_v2",
    df=enriched_df,
    mode="overwrite",
)
print("✅ Features written to Feature Store")

# COMMAND ----------
# MAGIC %md ## 5. Model Training with MLflow

# COMMAND ----------

df_train = enriched_df.toPandas()
FEATURE_COLS = [
    "tenure_months", "monthly_charge_eur", "total_charges_eur",
    "num_products", "support_tickets_6m", "payment_delay_count_12m",
    "avg_monthly_usage_gb", "days_since_last_contact", "nps_score",
    "contract_type_encoded", "payment_method_encoded",
    "has_internet_service", "has_phone_service",
    "charge_per_month", "ticket_rate", "product_engagement", "tenure_bucket"
]
available_features = [c for c in FEATURE_COLS if c in df_train.columns]

X = df_train[available_features]
y = df_train["churned"].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# SMOTE for imbalanced classes
smote = SMOTE(random_state=42, k_neighbors=5)
X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
print(f"After SMOTE: {pd.Series(y_train_res).value_counts().to_dict()}")

with mlflow.start_run(run_name="databricks-ensemble-v1.3") as run:
    mlflow.log_param("runtime", "databricks-ml-14.3")
    mlflow.log_param("feature_count", len(available_features))
    mlflow.log_param("train_size", len(X_train_res))

    # Ensemble model
    xgb = XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=6,
                         scale_pos_weight=2.5, random_state=42, tree_method="hist",
                         use_label_encoder=False, eval_metric="auc")
    lgbm = LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=63,
                           class_weight="balanced", random_state=42, verbose=-1)
    lr = LogisticRegression(C=1.0, class_weight="balanced", max_iter=500)

    ensemble = VotingClassifier(
        estimators=[("xgb", xgb), ("lgbm", lgbm), ("lr", lr)],
        voting="soft", weights=[3, 3, 1]
    )

    ensemble.fit(X_train_res, y_train_res)

    y_pred_proba = ensemble.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    auc = roc_auc_score(y_test, y_pred_proba)
    f1 = f1_score(y_test, y_pred)
    print(f"AUC: {auc:.4f} | F1: {f1:.4f}")

    mlflow.log_metrics({"auc_roc": auc, "f1_score": f1})
    mlflow.sklearn.log_model(ensemble, "churn_model",
                              registered_model_name="churn-prediction-ensemble")

    print(f"✅ Model logged. Run: {run.info.run_id}")

# COMMAND ----------
# MAGIC %md ## 6. SHAP Explainability

# COMMAND ----------

explainer = shap.TreeExplainer(xgb)
shap_values = explainer.shap_values(X_test.values[:500])

shap.summary_plot(shap_values, X_test.iloc[:500], feature_names=available_features,
                  show=False, plot_type="bar")
plt.title("SHAP Feature Importance — Churn Model")
plt.tight_layout()
plt.savefig("/dbfs/tmp/shap_importance.png", dpi=150)
mlflow.log_artifact("/dbfs/tmp/shap_importance.png")
display(plt.gcf())

# COMMAND ----------
# MAGIC %md ## 7. Model Registration & Promotion

# COMMAND ----------

from mlflow.tracking import MlflowClient

client = MlflowClient()
model_name = "churn-prediction-ensemble"

# Get latest version
latest_versions = client.get_latest_versions(model_name, stages=["None"])
latest_version = latest_versions[0].version

# Transition to Staging
client.transition_model_version_stage(
    name=model_name,
    version=latest_version,
    stage="Staging",
    archive_existing_versions=True,
)
print(f"✅ Model v{latest_version} promoted to Staging")

# If AUC meets threshold → promote to Production
if auc >= 0.85:
    client.transition_model_version_stage(
        name=model_name,
        version=latest_version,
        stage="Production",
        archive_existing_versions=True,
    )
    print(f"✅ Model v{latest_version} promoted to Production (AUC={auc:.4f})")
else:
    print(f"⚠️ Model v{latest_version} kept in Staging (AUC={auc:.4f} < 0.85)")

# COMMAND ----------
# MAGIC %md ## 8. Batch Scoring (Nightly Job)

# COMMAND ----------

# Load production model
prod_model = mlflow.sklearn.load_model(f"models:/{model_name}/Production")

# Score all active customers
all_customers = spark.table("gold.customer_churn_features_v2").toPandas()
X_all = all_customers[available_features].fillna(0)
churn_proba = prod_model.predict_proba(X_all)[:, 1]

all_customers["churn_probability"] = churn_proba
all_customers["churn_label"] = (churn_proba >= 0.5).astype(int)
all_customers["risk_level"] = pd.cut(churn_proba, bins=[0, 0.3, 0.55, 0.75, 1.01],
                                      labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"])
all_customers["scored_at"] = pd.Timestamp.now()

# Write scores to Gold layer
scores_df = spark.createDataFrame(all_customers[["customer_token", "churn_probability",
                                                    "churn_label", "risk_level", "scored_at"]])
scores_df.write.mode("append").saveAsTable("gold.churn_scores")
print(f"✅ Scored {len(all_customers):,} customers. High risk: {(churn_proba >= 0.55).sum():,}")
