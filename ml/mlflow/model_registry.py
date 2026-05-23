"""
MLflow Model Registry Promotion Workflow
Handles model lifecycle: None → Staging → Production → Archived.
Enforces QA gates before any promotion.
"""

import logging
import mlflow
from mlflow.tracking import MlflowClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

QA_GATES = {
    "churn-prediction-ensemble":     {"auc_roc": 0.85, "f1_score": 0.78},
    "customer-segmentation-kmeans":  {"silhouette_score": 0.60},
    "anomaly-isolation-forest":      {"precision": 0.80, "recall": 0.75},
}


def promote_model(model_name: str, version: str, target_stage: str, force: bool = False) -> bool:
    """
    Promote a model version to the target stage with QA gate enforcement.
    Returns True on success.
    """
    client = MlflowClient()
    mv = client.get_model_version(model_name, version)
    run = client.get_run(mv.run_id)
    metrics = run.data.metrics

    gates = QA_GATES.get(model_name, {})
    gate_failures = []

    for metric, threshold in gates.items():
        actual = metrics.get(metric, 0.0)
        if actual < threshold:
            gate_failures.append(f"{metric}={actual:.4f} < {threshold}")

    if gate_failures and not force:
        logger.error("❌ QA gates FAILED for %s v%s → %s:", model_name, version, target_stage)
        for f in gate_failures:
            logger.error("   %s", f)
        return False

    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage=target_stage,
        archive_existing_versions=True,
    )
    logger.info("✅ %s v%s promoted to %s", model_name, version, target_stage)
    return True


def get_production_model_info(model_name: str) -> dict:
    """Return metadata of the current production model."""
    client = MlflowClient()
    versions = client.get_latest_versions(model_name, stages=["Production"])
    if not versions:
        return {}
    mv = versions[0]
    run = client.get_run(mv.run_id)
    return {
        "name": model_name, "version": mv.version,
        "stage": mv.current_stage, "run_id": mv.run_id,
        "metrics": run.data.metrics, "params": run.data.params,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--version",    required=True)
    parser.add_argument("--stage",      default="Staging",
                        choices=["Staging", "Production", "Archived"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    mlflow.set_tracking_uri("http://localhost:5000")
    promote_model(args.model_name, args.version, args.stage, args.force)
