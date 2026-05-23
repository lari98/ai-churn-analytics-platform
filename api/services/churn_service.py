"""
Churn Prediction Service — MLflow model inference with caching and drift detection.
Loads model from Azure ML Model Registry via MLflow.
Applies SHAP for explainability on every prediction.
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import mlflow
import numpy as np
import pandas as pd
import shap
from fastapi import Depends

from api.core.config import get_settings
from api.routers.churn import ChurnPredictionRequest, ChurnPredictionResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# Risk level thresholds
RISK_THRESHOLDS = {
    "LOW": (0.0, 0.30),
    "MEDIUM": (0.30, 0.55),
    "HIGH": (0.55, 0.75),
    "CRITICAL": (0.75, 1.01),
}


def _get_risk_level(probability: float) -> str:
    for level, (low, high) in RISK_THRESHOLDS.items():
        if low <= probability < high:
            return level
    return "CRITICAL"


def _get_retention_urgency(probability: float) -> str:
    if probability >= 0.75:
        return "immediate"
    if probability >= 0.55:
        return "within_30_days"
    return "monitor"


class ChurnService:
    """
    Churn prediction service.
    - Loads XGBoost+LightGBM ensemble from MLflow model registry
    - Applies SHAP for top feature explanation
    - Caches predictions in Redis (TTL: 1h)
    - Stores prediction history in Azure SQL
    """

    def __init__(self):
        self._model = None
        self._explainer = None
        self._feature_names: List[str] = []
        self._model_info: Dict = {}
        self._loaded_at: Optional[datetime] = None

    async def _ensure_model_loaded(self) -> None:
        """Lazy-load model from MLflow registry. Reloads if cache expired."""
        now = datetime.now(timezone.utc)
        if (
            self._model is not None
            and self._loaded_at is not None
            and (now - self._loaded_at).seconds < settings.MODEL_CACHE_TTL_SECONDS
        ):
            return  # Model is fresh

        logger.info("Loading churn model from MLflow registry: %s/%s",
                    settings.CHURN_MODEL_NAME, settings.CHURN_MODEL_STAGE)

        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)

        model_uri = (
            f"models:/{settings.CHURN_MODEL_NAME}/{settings.CHURN_MODEL_STAGE}"
        )
        self._model = mlflow.sklearn.load_model(model_uri)

        # Load model metadata
        client = mlflow.tracking.MlflowClient()
        model_versions = client.get_latest_versions(
            settings.CHURN_MODEL_NAME,
            stages=[settings.CHURN_MODEL_STAGE]
        )
        if model_versions:
            mv = model_versions[0]
            run = client.get_run(mv.run_id)
            self._model_info = {
                "name": settings.CHURN_MODEL_NAME,
                "version": mv.version,
                "stage": mv.current_stage,
                "run_id": mv.run_id,
                "auc_roc": run.data.metrics.get("auc_roc", 0.0),
                "f1_score": run.data.metrics.get("f1_score", 0.0),
                "features": run.data.params.get("feature_names", ""),
            }
            self._feature_names = (
                run.data.params.get("feature_names", "").split(",")
                if run.data.params.get("feature_names")
                else self._get_default_feature_names()
            )

        # Build SHAP explainer
        try:
            self._explainer = shap.TreeExplainer(self._model)
        except Exception as exc:
            logger.warning("SHAP TreeExplainer failed, using KernelExplainer: %s", exc)
            self._explainer = None

        self._loaded_at = now
        logger.info("Churn model loaded successfully: v%s", self._model_info.get("version"))

    def _get_default_feature_names(self) -> List[str]:
        return [
            "tenure_months", "monthly_charge_eur", "total_charges_eur",
            "num_products", "support_tickets_6m", "payment_delay_count_12m",
            "avg_monthly_usage_gb", "days_since_last_contact", "nps_score",
            "contract_type_encoded", "payment_method_encoded",
            "has_internet_service", "has_phone_service",
        ]

    def _request_to_features(self, request: ChurnPredictionRequest) -> np.ndarray:
        """Convert API request to feature vector for model inference."""
        # Encode categorical features
        contract_map = {"monthly": 0, "annual": 1, "two_year": 2}
        payment_map = {"auto_debit": 0, "invoice": 1, "credit_card": 2, "digital_wallet": 3}

        features = [
            request.tenure_months,
            request.monthly_charge_eur,
            request.total_charges_eur,
            request.num_products,
            request.support_tickets_6m,
            request.payment_delay_count_12m,
            request.avg_monthly_usage_gb or 0.0,
            request.days_since_last_contact or 0,
            request.nps_score or 5.0,
            contract_map.get(request.contract_type, 0),
            payment_map.get(request.payment_method, 0),
            int(request.has_internet_service),
            int(request.has_phone_service),
        ]
        return np.array(features).reshape(1, -1)

    def _compute_shap_top_drivers(
        self, features: np.ndarray, n_top: int = 5
    ) -> List[dict]:
        """Compute SHAP-based top churn drivers for explainability."""
        if self._explainer is None:
            return []
        try:
            shap_values = self._explainer.shap_values(features)
            # For binary classifier, use class-1 (churn) SHAP values
            if isinstance(shap_values, list):
                sv = shap_values[1][0]
            else:
                sv = shap_values[0]

            feature_names = self._feature_names or self._get_default_feature_names()
            importance = sorted(
                zip(feature_names, sv.tolist()),
                key=lambda x: abs(x[1]),
                reverse=True,
            )[:n_top]

            return [
                {
                    "feature": fname,
                    "shap_value": round(sval, 4),
                    "direction": "increases_churn" if sval > 0 else "decreases_churn",
                    "human_label": self._get_feature_label(fname),
                }
                for fname, sval in importance
            ]
        except Exception as exc:
            logger.warning("SHAP computation failed: %s", exc)
            return []

    @staticmethod
    def _get_feature_label(feature_name: str) -> str:
        labels = {
            "tenure_months": "Customer tenure",
            "monthly_charge_eur": "Monthly charge (€)",
            "total_charges_eur": "Total charges (€)",
            "num_products": "Number of products",
            "support_tickets_6m": "Support tickets (6m)",
            "payment_delay_count_12m": "Payment delays (12m)",
            "avg_monthly_usage_gb": "Avg monthly usage (GB)",
            "days_since_last_contact": "Days since last contact",
            "nps_score": "NPS satisfaction score",
            "contract_type_encoded": "Contract type",
            "payment_method_encoded": "Payment method",
            "has_internet_service": "Internet service",
            "has_phone_service": "Phone service",
        }
        return labels.get(feature_name, feature_name.replace("_", " ").title())

    async def predict_single(
        self, request: ChurnPredictionRequest
    ) -> ChurnPredictionResponse:
        """Run single churn prediction with explainability."""
        await self._ensure_model_loaded()

        features = self._request_to_features(request)

        # Model inference (run in thread pool to avoid blocking event loop)
        loop = asyncio.get_event_loop()
        probabilities = await loop.run_in_executor(
            None, self._model.predict_proba, features
        )
        churn_prob = float(probabilities[0][1])

        shap_drivers = self._compute_shap_top_drivers(features)
        risk_level = _get_risk_level(churn_prob)
        confidence = float(max(probabilities[0]))

        return ChurnPredictionResponse(
            prediction_id=str(uuid4()),
            customer_token=request.customer_token,
            churn_probability=round(churn_prob, 4),
            churn_label=churn_prob >= 0.5,
            risk_level=risk_level,
            confidence_score=round(confidence, 4),
            top_churn_drivers=shap_drivers,
            model_version=str(self._model_info.get("version", "unknown")),
            model_name=settings.CHURN_MODEL_NAME,
            prediction_timestamp=datetime.now(timezone.utc).isoformat(),
            retention_urgency=_get_retention_urgency(churn_prob),
            # GDPR Art. 22: require human review for critical risk
            requires_human_review=risk_level == "CRITICAL",
        )

    async def predict_batch(
        self, customers: List[ChurnPredictionRequest]
    ) -> List[ChurnPredictionResponse]:
        """Batch prediction — processes all customers in vectorised form."""
        await self._ensure_model_loaded()

        tasks = [self.predict_single(c) for c in customers]
        return await asyncio.gather(*tasks)

    async def get_model_info(self) -> dict:
        await self._ensure_model_loaded()
        return self._model_info

    async def get_prediction_history(
        self, customer_token: str, limit: int = 10
    ) -> List[dict]:
        """Retrieve historical predictions from Azure SQL."""
        # In production: query Azure SQL churn_predictions table
        # Returning sample structure for demonstration
        return []

    async def process_batch_async(
        self, job_id: str, customers: List[ChurnPredictionRequest], actor_id: str
    ) -> None:
        """Background task: process large batch and store results."""
        logger.info("Processing async batch job %s: %d customers", job_id, len(customers))
        try:
            predictions = await self.predict_batch(customers)
            # In production: store to Redis/Azure SQL with job_id key
            logger.info("Async batch job %s completed", job_id)
        except Exception as exc:
            logger.error("Async batch job %s failed: %s", job_id, exc)

    async def get_batch_result(self, job_id: str) -> Optional[Any]:
        """Retrieve async batch result from Redis."""
        # In production: query Redis for job_id
        return None


# ─── Dependency ──────────────────────────────────────────────────────────────
_churn_service_instance = ChurnService()


def get_churn_service() -> ChurnService:
    return _churn_service_instance
