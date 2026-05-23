# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Feature Engineering Pipeline
# MAGIC ## Produces Silver → Gold feature tables for ML training

# COMMAND ----------
from pyspark.sql import functions as F, Window
from databricks.feature_store import FeatureStoreClient

fs = FeatureStoreClient()

# COMMAND ----------
# MAGIC %md ## RFM Feature Computation

# COMMAND ----------
customers = spark.table("silver.customers")
transactions = spark.table("silver.transactions")

# Recency: days since last transaction
latest_tx = transactions.groupBy("customer_token").agg(
    F.max("transaction_date").alias("last_tx_date")
)
customers = customers.join(latest_tx, "customer_token", "left")
customers = customers.withColumn(
    "recency_days",
    F.datediff(F.current_date(), F.col("last_tx_date")).cast("int")
)

# Frequency: transactions in last 6 months
tx_6m = transactions.filter(
    F.col("transaction_date") >= F.date_sub(F.current_date(), 180)
).groupBy("customer_token").agg(F.count("*").alias("frequency_6m"))
customers = customers.join(tx_6m, "customer_token", "left").fillna(0, ["frequency_6m"])

# Monetary: total spend in last 6 months
spend_6m = transactions.filter(
    F.col("transaction_date") >= F.date_sub(F.current_date(), 180)
).groupBy("customer_token").agg(F.sum("transaction_amount_eur").alias("monetary_6m_eur"))
customers = customers.join(spend_6m, "customer_token", "left").fillna(0.0, ["monetary_6m_eur"])

# COMMAND ----------
# MAGIC %md ## Engineered Features

# COMMAND ----------
customers = customers.withColumns({
    "charge_per_month":      F.col("total_charges_eur") / (F.col("tenure_months") + 1),
    "ticket_rate":           F.col("support_tickets_6m") / (F.col("tenure_months") + 1) * 6,
    "product_engagement":    F.col("num_products") * F.coalesce(F.col("avg_monthly_usage_gb"), F.lit(0)),
    "tenure_bucket":         F.when(F.col("tenure_months") <= 6, 0)
                              .when(F.col("tenure_months") <= 12, 1)
                              .when(F.col("tenure_months") <= 24, 2)
                              .when(F.col("tenure_months") <= 48, 3)
                              .otherwise(4),
    "contract_type_encoded": F.when(F.col("contract_type") == "monthly", 0)
                              .when(F.col("contract_type") == "annual", 1)
                              .otherwise(2),
    "payment_method_encoded":F.when(F.col("payment_method") == "auto_debit", 0)
                              .when(F.col("payment_method") == "invoice", 1)
                              .when(F.col("payment_method") == "credit_card", 2)
                              .otherwise(3),
})

# COMMAND ----------
# MAGIC %md ## Write to Feature Store (Gold Layer)

# COMMAND ----------
FEATURE_TABLE = "gold.customer_churn_features_v2"
fs.write_table(name=FEATURE_TABLE, df=customers, mode="overwrite")
print(f"✅ Feature table written: {FEATURE_TABLE} — {customers.count():,} rows")
display(customers.limit(3))
