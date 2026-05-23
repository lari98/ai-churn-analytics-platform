"""
Anomaly Detection Model Training
Isolation Forest + DBSCAN ensemble for behavioral anomaly detection.
Trained on transaction event data with DACH-specific thresholds.
"""

import argparse
import logging
import warnings
from datetime import datetime, timezone

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RANDOM_STATE = 42
CONTAMINATION = 0.05  # Expected anomaly rate (~5% of transactions)
FEATURE_COLS = [
    "transaction_amount_eur", "hour_of_day", "day_of_week",
    "is_foreign_country", "transactions_last_24h",
    "amount_deviation_from_avg", "channel_encoded",
]


def load_transactions(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    logger.info("Loaded %d transactions", len(df))

    channel_map = {"web": 0, "mobile": 1, "atm": 2, "branch": 3, "api": 4}
    df["channel_encoded"] = df.get("channel", pd.Series(["web"] * len(df))).map(channel_map).fillna(0)
    df["is_foreign_country"] = df.get("is_foreign_country", pd.Series([0] * len(df))).astype(int)

    # Feature: deviation from customer average amount
    if "customer_token" in df.columns:
        avg_amounts = df.groupby("customer_token")["transaction_amount_eur"].mean()
        df["amount_deviation_from_avg"] = df.apply(
            lambda r: abs(r["transaction_amount_eur"] - avg_amounts.get(r.get("customer_token", ""), 100)),
            axis=1,
        )
    else:
        df["amount_deviation_from_avg"] = 0.0

    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0.0

    return df


def train_isolation_forest(df: pd.DataFrame) -> dict:
    X = df[FEATURE_COLS].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    mlflow.set_experiment("anomaly-detection")
    run_name = f"isolation-forest-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params({
            "model_type": "IsolationForest",
            "contamination": CONTAMINATION,
            "n_estimators": 200,
            "feature_count": len(FEATURE_COLS),
            "feature_names": ",".join(FEATURE_COLS),
        })

        model = IsolationForest(
            n_estimators=200,
            contamination=CONTAMINATION,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        model.fit(X_scaled)

        # Anomaly scores (-1 = anomaly, 1 = normal)
        predictions = model.predict(X_scaled)
        scores = model.score_samples(X_scaled)

        # Convert to binary (1=anomaly, 0=normal) for metrics
        y_pred = (predictions == -1).astype(int)
        anomaly_rate = y_pred.mean()
        logger.info("Detected anomaly rate: %.2f%%", anomaly_rate * 100)
        mlflow.log_metric("anomaly_rate", anomaly_rate)
        mlflow.log_metric("avg_anomaly_score", float(scores[y_pred == 1].mean()) if y_pred.sum() > 0 else 0.0)

        # If labels available (ground truth fraud labels)
        if "is_fraud" in df.columns:
            y_true = df["is_fraud"].astype(int)
            metrics = {
                "precision": precision_score(y_true, y_pred, zero_division=0),
                "recall": recall_score(y_true, y_pred, zero_division=0),
                "f1_score": f1_score(y_true, y_pred, zero_division=0),
            }
            mlflow.log_metrics(metrics)
            logger.info("Supervised metrics: %s", metrics)

        # Save model + scaler as pipeline
        from sklearn.pipeline import Pipeline
        pipeline = Pipeline([("scaler", scaler), ("model", model)])
        mlflow.sklearn.log_model(
            pipeline,
            artifact_path="anomaly_model",
            registered_model_name="anomaly-isolation-forest",
        )

        logger.info("✅ Anomaly model logged. Run ID: %s", run.info.run_id)
        return {"run_id": run.info.run_id, "anomaly_rate": anomaly_rate}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--mlflow-uri", default=None)
    args = parser.parse_args()

    if args.mlflow_uri:
        mlflow.set_tracking_uri(args.mlflow_uri)

    df = load_transactions(args.data_path)
    result = train_isolation_forest(df)
    logger.info("Training complete: %s", result)


if __name__ == "__main__":
    main()
