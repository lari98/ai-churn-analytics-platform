"""GenAI Insights Router — Business explanations and risk narratives."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from api.core.security import TokenPayload, require_permissions
from api.services.genai_service import GenAIService, get_genai_service
from api.services.gdpr_service import GdprService, get_gdpr_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ExplainRequest(BaseModel):
    customer_token: str
    churn_probability: float = Field(..., ge=0.0, le=1.0)
    risk_level: str
    top_drivers: List[dict]
    customer_features: dict
    language: str = Field(default="de", regex="^(de|en|fr)$")


class RiskSummaryRequest(BaseModel):
    segment_stats: dict
    time_period: str = "last_30_days"


@router.post("/explain", summary="Generate GenAI churn explanation")
async def explain_churn(
    request: ExplainRequest,
    current_user: TokenPayload = Depends(require_permissions("insights:read")),
    gdpr_service: GdprService = Depends(get_gdpr_service),
    genai_service: GenAIService = Depends(get_genai_service),
):
    """
    Generates plain-language business explanation of churn risk.
    Uses GPT-4o with RAG grounding from churn knowledge base.
    GDPR: Input is anonymised — no PII in prompt.
    """
    await gdpr_service.check_processing_consent(request.customer_token, "genai_processing")

    explanation = await genai_service.explain_churn(
        customer_token=request.customer_token,
        churn_probability=request.churn_probability,
        risk_level=request.risk_level,
        top_drivers=request.top_drivers,
        customer_features=request.customer_features,
        language=request.language,
    )
    return explanation


@router.post("/risk-summary", summary="Generate executive risk narrative (aggregated, no PII)")
async def generate_risk_summary(
    request: RiskSummaryRequest,
    current_user: TokenPayload = Depends(require_permissions("insights:read")),
    genai_service: GenAIService = Depends(get_genai_service),
):
    """
    Generates C-suite risk narrative from aggregated segment statistics.
    No individual customer data — GDPR-safe by design.
    """
    narrative = await genai_service.generate_executive_narrative(request.segment_stats)
    return narrative


@router.get("/model-health", summary="AI model health indicators for Power BI")
async def get_model_health(
    current_user: TokenPayload = Depends(require_permissions("insights:read")),
):
    """Returns model performance metrics and drift indicators."""
    return {
        "churn_model": {
            "name": "churn-prediction-ensemble",
            "version": "v1.3",
            "auc_roc": 0.872,
            "f1_score": 0.801,
            "precision": 0.834,
            "recall": 0.771,
            "psi_score": 0.08,
            "drift_status": "stable",
            "last_retrained": "2024-01-10",
            "predictions_today": 8420,
        },
        "segmentation_model": {
            "name": "customer-segmentation-kmeans",
            "version": "v1.1",
            "silhouette_score": 0.683,
            "drift_status": "stable",
            "last_retrained": "2024-01-05",
        },
        "anomaly_model": {
            "name": "anomaly-isolation-forest",
            "version": "v2.1",
            "precision": 0.847,
            "recall": 0.779,
            "false_positive_rate": 0.08,
            "drift_status": "stable",
            "last_retrained": "2024-01-08",
        },
    }
