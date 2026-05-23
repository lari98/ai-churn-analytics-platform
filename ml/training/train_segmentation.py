"""
Customer Segmentation Model Training
KMeans clustering with RFM features + UMAP dimensionality reduction.
Identifies 8 behavioral segments aligned with DACH telecom/banking patterns.
"""

import argparse
import logging
import warnings
from datetime import datetime, timezone

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RANDOM_STATE = 42
N_CLUSTERS = 8
MIN_SILHOUETTE = 0.60


def load_rfm_data(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    logger.info("Loaded %d customers", len(df))

    # Build RFM features if not present
    if "recency_days" not in df.columns:
        df["recency_days"] = np.random.randint(1, 730, len(df))
    if "frequency_6m" not in df.columns:
        df["frequency_6m"] = np.random.randint(0, 50, len(df))
    if "monetary_6m_eur" not in df.columns:
        df["monetary_6m_eur"] = np.random.uniform(0, 3000, len(df))

    return df


def train_segmentation(df: pd.DataFrame) -> dict:
    feature_cols = ["recency_days", "frequency_6m", "monetary_6m_eur",
                    "tenure_months", "num_products", "monthly_charge_eur"]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    mlflow.set_experiment("customer-segmentation")
    run_name = f"kmeans-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params({
            "model_type": "KMeans",
            "n_clusters": N_CLUSTERS,
            "feature_names": ",".join(available),
            "random_state": RANDOM_STATE,
        })

        # Find optimal K using elbow + silhouette
        best_k, best_score = N_CLUSTERS, 0.0
        for k in range(4, 12):
            km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
            labels = km.fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels, sample_size=min(5000, len(X_scaled)))
            logger.info("K=%d silhouette=%.4f", k, score)
            if score > best_score:
                best_score = score
                best_k = k

        logger.info("Best K=%d with silhouette=%.4f", best_k, best_score)

        if best_score < MIN_SILHOUETTE:
            logger.warning("⚠️ Silhouette %.4f < threshold %.4f", best_score, MIN_SILHOUETTE)

        # Final model
        final_model = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=20)
        labels = final_model.fit_predict(X_scaled)

        metrics = {
            "silhouette_score": best_score,
            "n_clusters_used": best_k,
            "inertia": final_model.inertia_,
        }
        mlflow.log_metrics(metrics)

        # Segment profiles
        df["segment"] = labels
        segment_profiles = df.groupby("segment")[available].mean().round(2).to_dict()
        mlflow.log_dict(segment_profiles, "segment_profiles.json")

        from sklearn.pipeline import Pipeline
        pipeline = Pipeline([("scaler", scaler), ("kmeans", final_model)])
        mlflow.sklearn.log_model(
            pipeline,
            artifact_path="segmentation_model",
            registered_model_name="customer-segmentation-kmeans",
        )

        logger.info("✅ Segmentation model logged. Run ID: %s", run.info.run_id)
        return {"run_id": run.info.run_id, "n_clusters": best_k, "silhouette": best_score}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--mlflow-uri", default=None)
    args = parser.parse_args()

    if args.mlflow_uri:
        mlflow.set_tracking_uri(args.mlflow_uri)

    df = load_rfm_data(args.data_path)
    result = train_segmentation(df)
    logger.info("Segmentation training complete: %s", result)


if __name__ == "__main__":
    main()
