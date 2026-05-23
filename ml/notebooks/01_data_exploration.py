# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Data Exploration & EDA
# MAGIC ## DACH Customer Churn Analytics Platform
# MAGIC ### Databricks Runtime 14.3 ML | PySpark 3.5

# COMMAND ----------
# MAGIC %md ## Setup

# COMMAND ----------
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pyspark.sql import functions as F

spark.conf.set("spark.sql.adaptive.enabled", "true")
print("✅ Imports complete")

# COMMAND ----------
# MAGIC %md ## Load Bronze Layer Data (anonymised)

# COMMAND ----------
customers = spark.table("bronze.customers_anonymised")
transactions = spark.table("bronze.transactions_anonymised")
interactions = spark.table("bronze.interactions_anonymised")

print(f"Customers:    {customers.count():>10,}")
print(f"Transactions: {transactions.count():>10,}")
print(f"Interactions: {interactions.count():>10,}")

# COMMAND ----------
# MAGIC %md ## Churn Rate Analysis

# COMMAND ----------
churn_rate = customers.agg(F.mean("churned").alias("churn_rate")).collect()[0]["churn_rate"]
print(f"Overall churn rate: {churn_rate:.2%}")
display(customers.groupBy("churned").count().withColumn("pct", F.col("count") / customers.count() * 100))

# COMMAND ----------
# MAGIC %md ## Feature Distributions

# COMMAND ----------
df = customers.toPandas()
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
fig.suptitle("DACH Customer Feature Distributions", fontsize=14)

for ax, col in zip(axes.flatten(), ["tenure_months","monthly_charge_eur","support_tickets_6m","nps_score","num_products","payment_delay_count_12m"]):
    sns.histplot(data=df, x=col, hue="churned", ax=ax, bins=20, alpha=0.7)
    ax.set_title(col)

plt.tight_layout()
display(fig)

# COMMAND ----------
# MAGIC %md ## Correlation Heatmap

# COMMAND ----------
numeric_cols = ["tenure_months","monthly_charge_eur","support_tickets_6m","nps_score","payment_delay_count_12m","churned"]
corr = df[numeric_cols].corr()
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
ax.set_title("Feature Correlations with Churn")
display(fig)

# COMMAND ----------
# MAGIC %md ## Churn by Contract Type & Region

# COMMAND ----------
display(customers.groupBy("contract_type", "churned").count().orderBy("contract_type", "churned"))
display(customers.groupBy("region").agg(F.mean("churned").alias("churn_rate")).orderBy(F.desc("churn_rate")))

# COMMAND ----------
# MAGIC %md ## Data Quality Report

# COMMAND ----------
null_counts = {c: customers.filter(F.col(c).isNull()).count() for c in customers.columns}
print("Null counts per column:")
for col, cnt in sorted(null_counts.items(), key=lambda x: x[1], reverse=True):
    if cnt > 0:
        print(f"  {col:40s}: {cnt:5d} ({cnt/customers.count():.1%})")
print("\n✅ EDA complete — proceed to 02_feature_engineering.py")
