"""
Churn Prediction Router — Real-time and batch churn scoring endpoints.
Implements RBAC, audit logging, PII masking, and GDPR consent checks.
"""

import logging
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator

from api.core.security import TokenPayload, get_current_user, require_permissions
from api.middleware.audit_log import AuditEvent, AuditEventType, AuditOutcome
from api.services.churn_service import ChurnService, get_churn_service
from api.services.gdpr_service import GdprService, get_gdpr_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Request / Response Schemas ──────────────────────────────────────────────

class ChurnPredictionRequest(BaseModel):
    """
    Input for single customer churn prediction.
    All fields are anonymised (no raw PII — use customer_token, not name/email).
    """
    customer_token: str = Field(
        ...,
        description="Pseudonymous customer identifier (HMAC token, not raw ID)",
        min_length=8, max_length=128,
    )
    # Anonymised features (no PII)
    tenure_months: int = Field(..., ge=0, le=600, description="Months as customer")
    monthly_charge_eur: float = Field(..., ge=0.0, le=10000.0)
    total_charges_eur: float = Field(..., ge=0.0)
    num_products: int = Field(..., ge=1, le=20)
    contract_type: str = Field(..., regex="^(monthly|annual|two_year)$")
    payment_method: str = Field(..., regex="^(auto_debit|invoice|credit_card|digital_wallet)$")
    has_internet_service: bool
    has_phone_service: bool
    support_tickets_6m: int = Field(..., ge=0, le=100)
    avg_monthly_usage_gb: Optional[float] = Field(None, ge=0.0)
    days_since_last_contact: Optional[int] = Field(None, ge=0)
    nps_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    payment_delay_count_12m: int = Field(default=0, ge=0)

    @validator("tenure_months")
    def validate_tenure(cls, v):
        if v < 0:
            raise ValueError("tenure_months must be non-negative")
        return v


class ChurnPredictionResponse(BaseModel):
    """Churn prediction output with explainability."""
    prediction_id: str
    customer_token: str
    churn_probability: float = Field(..., ge=0.0, le=1.0)
    churn_label: bool
    risk_level: str  # LOW | MEDIUM | HIGH | CRITICAL
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    top_churn_drivers: List[dict]  # SHAP-based feature importance
    model_version: str
    model_name: str
    prediction_timestamp: str
    retention_urgency: str  # immediate | within_30_days | monitor
    requires_human_review: bool  # GDPR Art. 22 flag


class BatchChurnRequest(BaseModel):
    """Batch prediction for up to 1000 customers."""
    customers: List[ChurnPredictionRequest] = Field(..., min_items=1, max_items=1000)
    async_processing: bool = Field(
        default=False,
        description="If True, returns job_id for async result retrieval",
    )


class BatchChurnResponse(BaseModel):
    """Batch prediction results or job reference."""
    job_id: str
    total_customers: int
    predictions: Optional[List[ChurnPredictionResponse]] = None
    status: str  # completed | processing | failed
    high_risk_count: int = 0
    avg_churn_probability: float = 0.0


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post(
    "/predict",
    response_model=ChurnPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict churn probability for a single customer",
    description=(
        "Returns churn probability, risk level, SHAP-based top drivers, "
        "and retention urgency flag. Requires 'churn:read' permission."
    ),
)
async def predict_churn(
    request: ChurnPredictionRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenPayload = Depends(require_permissions("churn:read")),
    churn_service: ChurnService = Depends(get_churn_service),
    gdpr_service: GdprService = Depends(get_gdpr_service),
) -> ChurnPredictionResponse:
    """
    Endpoint: POST /api/v1/churn/predict

    GDPR: Checks consent before processing. Logs prediction to audit trail.
    GDPR Art. 22: Sets requires_human_review=True for high-stakes decisions.
    """
    # GDPR consent check — only process if customer consented to churn analytics
    await gdpr_service.check_processing_consent(
        customer_token=request.customer_token,
        purpose="churn_analytics",
    )

    prediction = await churn_service.predict_single(request)

    # Background audit log (non-blocking)
    background_tasks.add_task(
        _log_prediction_event,
        customer_token=request.customer_token,
        actor_id=current_user.sub,
        actor_role=current_user.roles[0] if current_user.roles else "unknown",
        churn_probability=prediction.churn_probability,
        risk_level=prediction.risk_level,
    )

    return prediction


@router.post(
    "/batch-predict",
    response_model=BatchChurnResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch churn prediction (up to 1000 customers)",
)
async def batch_predict_churn(
    request: BatchChurnRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenPayload = Depends(require_permissions("churn:read")),
    churn_service: ChurnService = Depends(get_churn_service),
) -> BatchChurnResponse:
    """
    Endpoint: POST /api/v1/churn/batch-predict

    For large batches (async_processing=True), returns a job_id.
    Poll GET /churn/batch-status/{job_id} for results.
    """
    job_id = str(uuid4())

    if request.async_processing:
        background_tasks.add_task(
            churn_service.process_batch_async,
            job_id=job_id,
            customers=request.customers,
            actor_id=current_user.sub,
        )
        return BatchChurnResponse(
            job_id=job_id,
            total_customers=len(request.customers),
            status="processing",
        )

    # Synchronous batch (≤ 100 customers recommended)
    predictions = await churn_service.predict_batch(request.customers)
    high_risk = [p for p in predictions if p.churn_probability >= 0.7]
    avg_prob = sum(p.churn_probability for p in predictions) / len(predictions)

    return BatchChurnResponse(
        job_id=job_id,
        total_customers=len(predictions),
        predictions=predictions,
        status="completed",
        high_risk_count=len(high_risk),
        avg_churn_probability=round(avg_prob, 4),
    )


@router.get(
    "/batch-status/{job_id}",
    response_model=BatchChurnResponse,
    summary="Poll batch prediction job status",
)
async def get_batch_status(
    job_id: str,
    current_user: TokenPayload = Depends(require_permissions("churn:read")),
    churn_service: ChurnService = Depends(get_churn_service),
) -> BatchChurnResponse:
    result = await churn_service.get_batch_result(job_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or expired",
        )
    return result


@router.get(
    "/history/{customer_token}",
    summary="Get churn prediction history for a customer",
)
async def get_churn_history(
    customer_token: str,
    limit: int = Query(default=10, ge=1, le=100),
    current_user: TokenPayload = Depends(require_permissions("churn:read")),
    churn_service: ChurnService = Depends(get_churn_service),
):
    """
    Returns historical churn predictions for trend analysis.
    Used by Power BI for churn trend dashboard.
    """
    history = await churn_service.get_prediction_history(customer_token, limit=limit)
    return {"customer_token": customer_token, "history": history}


@router.get(
    "/model-info",
    summary="Get deployed churn model metadata",
)
async def get_model_info(
    current_user: TokenPayload = Depends(require_permissions("churn:read")),
    churn_service: ChurnService = Depends(get_churn_service),
):
    """Returns model name, version, metrics, and feature list."""
    return await churn_service.get_model_info()


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _log_prediction_event(
    customer_token: str,
    actor_id: str,
    actor_role: str,
    churn_probability: float,
    risk_level: str,
) -> None:
    """Background task: write prediction to audit trail."""
    event = AuditEvent(
        event_type=AuditEventType.ML_PREDICTION,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="churn_model",
        resource_id=customer_token,
        action="PREDICT",
        outcome=AuditOutcome.SUCCESS,
        correlation_id=str(uuid4()),
        gdpr_basis="legitimate_interest",
        metadata={
            "churn_probability": churn_probability,
            "risk_level": risk_level,
        },
    )
    event.log()
