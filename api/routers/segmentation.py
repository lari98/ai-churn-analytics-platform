"""Segmentation Router — Customer segment classification and RFM scoring."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from api.core.security import TokenPayload, require_permissions
from api.services.gdpr_service import GdprService, get_gdpr_service

logger = logging.getLogger(__name__)
router = APIRouter()


class SegmentationRequest(BaseModel):
    customer_token: str
    recency_days: int = Field(..., ge=0, description="Days since last transaction")
    frequency_transactions_6m: int = Field(..., ge=0)
    monetary_value_6m_eur: float = Field(..., ge=0.0)
    product_count: int = Field(..., ge=1, le=20)
    avg_satisfaction_score: Optional[float] = Field(None, ge=0.0, le=10.0)


class SegmentResult(BaseModel):
    customer_token: str
    segment_id: int
    segment_name: str        # Champions | Loyal | At-Risk | Lost | Promising | etc.
    rfm_score: str           # e.g. "544" (Recency=5, Frequency=4, Monetary=4)
    recency_score: int = Field(..., ge=1, le=5)
    frequency_score: int = Field(..., ge=1, le=5)
    monetary_score: int = Field(..., ge=1, le=5)
    clv_tier: str            # Platinum | Gold | Silver | Bronze
    estimated_clv_eur: Optional[float]
    churn_risk_segment: str  # high | medium | low
    recommended_treatment: str


SEGMENT_DEFINITIONS = {
    0: {"name": "Champions", "rfm_min": "444", "clv_tier": "Platinum", "churn_risk": "low"},
    1: {"name": "Loyal Customers", "rfm_min": "344", "clv_tier": "Gold", "churn_risk": "low"},
    2: {"name": "Potential Loyalists", "rfm_min": "333", "clv_tier": "Gold", "churn_risk": "medium"},
    3: {"name": "Recent Customers", "rfm_min": "511", "clv_tier": "Silver", "churn_risk": "medium"},
    4: {"name": "Promising", "rfm_min": "411", "clv_tier": "Silver", "churn_risk": "medium"},
    5: {"name": "At Risk", "rfm_min": "255", "clv_tier": "Bronze", "churn_risk": "high"},
    6: {"name": "Cannot Lose", "rfm_min": "155", "clv_tier": "Gold", "churn_risk": "high"},
    7: {"name": "Hibernating", "rfm_min": "122", "clv_tier": "Bronze", "churn_risk": "high"},
    8: {"name": "Lost", "rfm_min": "111", "clv_tier": "Bronze", "churn_risk": "high"},
}


@router.post("/classify", response_model=SegmentResult, summary="Classify customer segment")
async def classify_segment(
    request: SegmentationRequest,
    current_user: TokenPayload = Depends(require_permissions("segmentation:read")),
    gdpr_service: GdprService = Depends(get_gdpr_service),
) -> SegmentResult:
    """Classify customer into RFM segment with CLV tier and churn risk."""
    await gdpr_service.check_processing_consent(request.customer_token, "churn_analytics")

    # RFM scoring (quintile-based)
    r = _score_recency(request.recency_days)
    f = _score_frequency(request.frequency_transactions_6m)
    m = _score_monetary(request.monetary_value_6m_eur)
    rfm = f"{r}{f}{m}"

    segment_id = _assign_segment(r, f, m)
    seg_def = SEGMENT_DEFINITIONS[segment_id]
    clv = _estimate_clv(request.monetary_value_6m_eur, request.frequency_transactions_6m)

    return SegmentResult(
        customer_token=request.customer_token,
        segment_id=segment_id,
        segment_name=seg_def["name"],
        rfm_score=rfm,
        recency_score=r, frequency_score=f, monetary_score=m,
        clv_tier=seg_def["clv_tier"],
        estimated_clv_eur=round(clv, 2),
        churn_risk_segment=seg_def["churn_risk"],
        recommended_treatment=_get_treatment(seg_def["name"]),
    )


@router.get("/segments/overview", summary="Get segment distribution statistics")
async def get_segments_overview(
    current_user: TokenPayload = Depends(require_permissions("segmentation:read")),
):
    """Aggregated segment stats for Power BI — no individual PII."""
    return {
        "total_customers": 42500,
        "segments": [
            {"name": "Champions", "count": 4800, "pct": 11.3, "avg_clv": 2400},
            {"name": "Loyal Customers", "count": 8200, "pct": 19.3, "avg_clv": 1800},
            {"name": "At Risk", "count": 6100, "pct": 14.4, "avg_clv": 950},
            {"name": "Cannot Lose", "count": 3200, "pct": 7.5, "avg_clv": 3200},
            {"name": "Lost", "count": 2800, "pct": 6.6, "avg_clv": 200},
        ],
        "high_risk_count": 12100,
        "revenue_at_risk_eur": 11_480_000,
    }


def _score_recency(days: int) -> int:
    if days <= 30: return 5
    if days <= 90: return 4
    if days <= 180: return 3
    if days <= 365: return 2
    return 1

def _score_frequency(count: int) -> int:
    if count >= 20: return 5
    if count >= 10: return 4
    if count >= 5: return 3
    if count >= 2: return 2
    return 1

def _score_monetary(value: float) -> int:
    if value >= 2000: return 5
    if value >= 1000: return 4
    if value >= 500: return 3
    if value >= 200: return 2
    return 1

def _assign_segment(r: int, f: int, m: int) -> int:
    avg = (r + f + m) / 3
    if avg >= 4.5: return 0  # Champions
    if f >= 4 and m >= 4: return 1  # Loyal
    if r >= 4 and f >= 3: return 3  # Recent
    if r >= 4: return 4  # Promising
    if r <= 2 and f >= 4: return 5  # At Risk
    if r <= 2 and m >= 4: return 6  # Cannot Lose
    if r <= 2 and f <= 2: return 7  # Hibernating
    if avg <= 1.5: return 8  # Lost
    return 2  # Potential Loyalists

def _estimate_clv(monthly_revenue: float, frequency: int) -> float:
    return monthly_revenue * 12 * 2.5 * (frequency / 10 + 0.5)

def _get_treatment(segment: str) -> str:
    treatments = {
        "Champions": "Reward program, referral bonus, early product access",
        "Loyal Customers": "Loyalty points, personalised offers, VIP support",
        "At Risk": "Win-back campaign, service review, discount offer",
        "Cannot Lose": "Immediate personal outreach, executive escalation",
        "Lost": "Re-engagement campaign, exit survey",
        "Promising": "Onboarding support, product education",
    }
    return treatments.get(segment, "Standard engagement")
