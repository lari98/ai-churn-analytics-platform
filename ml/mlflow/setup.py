"""
MLflow Server Configuration & Experiment Bootstrap
Sets up experiments, tags, and model registry for the platform.
Run once during environment provisioning.
"""

import logging
import os
import mlflow
from mlflow.tracking import MlflowClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

EXPERIMENTS = [
    {
        "name": "churn-prediction",
        "tags": {"team": "ml-engineering", "domain": "churn", "gdpr_compliant": "true"},
    },
    {
        "name": "customer-segmentation",
        "tags": {"team": "ml-engineering", "domain": "segmentation", "gdpr_compliant": "true"},
    },
    {
        "name": "anomaly-detection",
        "tags": {"team": "ml-engineering", "domain": "anomaly", "gdpr_compliant": "true"},
    },
]

REGISTERED_MODELS = [
    {
        "name": "churn-prediction-ensemble",
        "description": "XGBoost + LightGBM + LR ensemble for customer churn prediction. GDPR-compliant: no PII in features.",
        "tags": {"framework": "sklearn", "algorithm": "ensemble", "pii_in_features": "false"},
    },
    {
        "name": "customer-segmentation-kmeans",
        "description": "KMeans segmentation model with RFM features. 8 customer segments.",
        "tags": {"framework": "sklearn", "algorithm": "kmeans", "pii_in_features": "false"},
    },
    {
        "name": "anomaly-isolation-forest",
        "description": "Isolation Forest for real-time transaction anomaly detection.",
        "tags": {"framework": "sklearn", "algorithm": "isolation_forest", "pii_in_features": "false"},
    },
]


def setup_mlflow():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    logger.info("Setting up MLflow experiments...")
    for exp in EXPERIMENTS:
        try:
            experiment_id = mlflow.create_experiment(exp["name"], tags=exp["tags"])
            logger.info("  Created experiment: %s (id=%s)", exp["name"], experiment_id)
        except mlflow.exceptions.MlflowException:
            existing = mlflow.get_experiment_by_name(exp["name"])
            logger.info("  Experiment already exists: %s (id=%s)", exp["name"], existing.experiment_id)

    logger.info("Registering model placeholders...")
    for model in REGISTERED_MODELS:
        try:
            client.create_registered_model(
                name=model["name"],
                description=model["description"],
                tags=model["tags"],
            )
            logger.info("  Registered model: %s", model["name"])
        except mlflow.exceptions.MlflowException:
            logger.info("  Model already registered: %s", model["name"])

    logger.info("✅ MLflow setup complete. Tracking URI: %s", MLFLOW_TRACKING_URI)


if __name__ == "__main__":
    setup_mlflow()
