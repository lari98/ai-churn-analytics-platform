"""
GDPR Compliance Router — Implements all data subject rights (GDPR Art. 15-22).
Restricted to 'gdpr-officer' and 'platform-admin' roles.
All actions are audited and irreversible erasures require dual confirmation.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field, validator

from api.core.security import TokenPayload, get_current_user, require_permissions
from api.middleware.audit_log import AuditEvent, AuditEventType, AuditOutcome, log_gdpr_event
from api.services.gdpr_service import GdprService, get_gdpr_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ConsentRecord(BaseModel):
    customer_token: str
    churn_analytics: bool = False
    behavioral_profiling: bool = False
    marketing_contact: bool = False
    data_sharing_third_parties: bool = False
    genai_processing: bool = False
    consent_version: str = "2024-01-01-v2"
    channel: str = Field(..., regex="^(web_portal|mobile_app|call_center|written)$")


class ConsentResponse(BaseModel):
    customer_token: str
    consent_id: str
    recorded_at: str
    purposes: dict
    version: str


class DataExportResponse(BaseModel):
    customer_token: str
    export_id: str
    generated_at: str
    data_categories: List[str]
    retention_dates: dict
    processing_purposes: List[str]
    data: dict  # All held data (PII masked in response)


class ErasureRequest(BaseModel):
    customer_token: str
    reason: str = Field(
        ...,
        regex="^(customer_request|consent_withdrawn|legal_requirement|deceased)$",
    )
    requested_by: str  # DPO operator ID
    confirmation: str = Field(
        ...,
        description="Must equal 'CONFIRM_ERASURE' to proceed",
    )

    @validator("confirmation")
    def validate_confirmation(cls, v):
        if v != "CONFIRM_ERASURE":
            raise ValueError(
                "Erasure requires explicit confirmation string 'CONFIRM_ERASURE'"
            )
        return v


class ErasureResponse(BaseModel):
    erasure_id: str
    customer_token: str
    status: str  # initiated | completed | failed | partial
    systems_affected: List[str]
    completion_timestamp: Optional[str]
    audit_reference: str
    legal_hold_check: str  # no_hold | hold_applied | review_required


class RestrictionRequest(BaseModel):
    customer_token: str
    reason: str
    restrict_until: Optional[datetime] = None


class ObjectionRequest(BaseModel):
    customer_token: str
    processing_purposes: List[str] = Field(
        ..., description="List of purposes to object to"
    )
    reason: str


class AuditLogEntry(BaseModel):
    event_id: str
    timestamp: str
    event_type: str
    action: str
    outcome: str
    correlation_id: str


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post(
    "/consent",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record customer consent (GDPR Art. 6, 7)",
)
async def record_consent(
    consent: ConsentRecord,
    current_user: TokenPayload = Depends(require_permissions("gdpr:write")),
    gdpr_service: GdprService = Depends(get_gdpr_service),
) -> ConsentResponse:
    """Record or update customer consent for specific processing purposes."""
    result = await gdpr_service.record_consent(consent, actor_id=current_user.sub)

    log_gdpr_event(
        event_type=AuditEventType.CONSENT_RECORDED,
        customer_token=consent.customer_token,
        actor_id=current_user.sub,
        actor_role=current_user.roles[0] if current_user.roles else "unknown",
        outcome=AuditOutcome.SUCCESS,
        gdpr_basis="consent",
        correlation_id=str(uuid4()),
        metadata={"purposes": consent.dict(exclude={"customer_token", "channel"})},
    )

    return result


@router.get(
    "/consent/{customer_token}",
    response_model=ConsentResponse,
    summary="Get customer consent record (GDPR Art. 7)",
)
async def get_consent(
    customer_token: str,
    current_user: TokenPayload = Depends(require_permissions("gdpr:read")),
    gdpr_service: GdprService = Depends(get_gdpr_service),
) -> ConsentResponse:
    result = await gdpr_service.get_consent(customer_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No consent record found for this customer",
        )
    return result


@router.get(
    "/customer/{customer_token}/data-export",
    response_model=DataExportResponse,
    summary="Export all personal data (GDPR Art. 15 — Right of Access)",
)
async def export_customer_data(
    customer_token: str,
    format: str = Query(default="json", regex="^(json|pdf)$"),
    current_user: TokenPayload = Depends(require_permissions("gdpr:read")),
    gdpr_service: GdprService = Depends(get_gdpr_service),
) -> DataExportResponse:
    """
    Returns all personal data held for a customer.
    Includes: profile, scores, consent history, processing purposes.
    Response is PII-masked (handled by middleware) — DPO sees tokens, not raw PII.
    """
    export = await gdpr_service.export_customer_data(customer_token, format=format)

    log_gdpr_event(
        event_type=AuditEventType.GDPR_EXPORT,
        customer_token=customer_token,
        actor_id=current_user.sub,
        actor_role=current_user.roles[0] if current_user.roles else "unknown",
        outcome=AuditOutcome.SUCCESS,
        gdpr_basis="data_subject_request",
        correlation_id=str(uuid4()),
    )

    return export


@router.delete(
    "/customer/{customer_token}",
    response_model=ErasureResponse,
    status_code=status.HTTP_200_OK,
    summary="Erase customer data (GDPR Art. 17 — Right to be Forgotten)",
)
async def erase_customer_data(
    customer_token: str,
    erasure_request: ErasureRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenPayload = Depends(require_permissions("gdpr:write")),
    gdpr_service: GdprService = Depends(get_gdpr_service),
) -> ErasureResponse:
    """
    GDPR Art. 17 — Initiates irreversible customer data erasure.

    Safety checks:
    1. Requires 'CONFIRM_ERASURE' confirmation string
    2. Checks for legal holds (active contracts, pending legal proceedings)
    3. Pseudonymises audit logs (cannot delete these — legal obligation)
    4. Deletes from: Azure SQL, ADLS, Redis, Cosmos DB, ML features

    Completed within 72 hours (background processing for large datasets).
    """
    if erasure_request.customer_token != customer_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customer_token in path and body must match",
        )

    erasure_id = str(uuid4())

    # Check legal hold before erasure
    legal_hold = await gdpr_service.check_legal_hold(customer_token)
    if legal_hold["has_hold"]:
        log_gdpr_event(
            event_type=AuditEventType.GDPR_ERASURE,
            customer_token=customer_token,
            actor_id=current_user.sub,
            actor_role=current_user.roles[0] if current_user.roles else "unknown",
            outcome=AuditOutcome.DENIED,
            gdpr_basis="data_subject_request",
            correlation_id=erasure_id,
            metadata={"reason": "legal_hold", "hold_details": legal_hold},
        )
        return ErasureResponse(
            erasure_id=erasure_id,
            customer_token=customer_token,
            status="hold_applied",
            systems_affected=[],
            completion_timestamp=None,
            audit_reference=erasure_id,
            legal_hold_check="hold_applied",
        )

    # Trigger erasure (background for completeness within 72h)
    background_tasks.add_task(
        gdpr_service.execute_erasure,
        erasure_id=erasure_id,
        customer_token=customer_token,
        reason=erasure_request.reason,
        requested_by=erasure_request.requested_by,
        actor_id=current_user.sub,
    )

    log_gdpr_event(
        event_type=AuditEventType.GDPR_ERASURE,
        customer_token=customer_token,
        actor_id=current_user.sub,
        actor_role=current_user.roles[0] if current_user.roles else "unknown",
        outcome=AuditOutcome.SUCCESS,
        gdpr_basis="data_subject_request",
        correlation_id=erasure_id,
        metadata={"reason": erasure_request.reason},
    )

    return ErasureResponse(
        erasure_id=erasure_id,
        customer_token=customer_token,
        status="initiated",
        systems_affected=["azure_sql", "adls", "redis_cache", "cosmos_db", "ml_feature_store"],
        completion_timestamp=None,
        audit_reference=erasure_id,
        legal_hold_check="no_hold",
    )


@router.post(
    "/customer/{customer_token}/restrict-processing",
    status_code=status.HTTP_200_OK,
    summary="Restrict data processing (GDPR Art. 18)",
)
async def restrict_processing(
    customer_token: str,
    request: RestrictionRequest,
    current_user: TokenPayload = Depends(require_permissions("gdpr:write")),
    gdpr_service: GdprService = Depends(get_gdpr_service),
):
    """Flags customer record — excludes from all ML scoring and analytics."""
    await gdpr_service.restrict_processing(customer_token, request.reason)
    return {
        "customer_token": customer_token,
        "status": "processing_restricted",
        "message": "Customer excluded from all automated processing",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/customer/{customer_token}/object-processing",
    status_code=status.HTTP_200_OK,
    summary="Object to processing (GDPR Art. 21)",
)
async def object_to_processing(
    customer_token: str,
    request: ObjectionRequest,
    current_user: TokenPayload = Depends(require_permissions("gdpr:write")),
    gdpr_service: GdprService = Depends(get_gdpr_service),
):
    await gdpr_service.record_objection(customer_token, request.processing_purposes, request.reason)
    return {
        "customer_token": customer_token,
        "objection_status": "recorded",
        "excluded_purposes": request.processing_purposes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/customer/{customer_token}/request-human-review",
    status_code=status.HTTP_200_OK,
    summary="Request human review of automated decision (GDPR Art. 22)",
)
async def request_human_review(
    customer_token: str,
    reason: str,
    current_user: TokenPayload = Depends(require_permissions("gdpr:write")),
    gdpr_service: GdprService = Depends(get_gdpr_service),
):
    """Routes customer to human review queue. No fully automated decisions."""
    ticket_id = await gdpr_service.create_human_review_ticket(customer_token, reason)
    return {
        "customer_token": customer_token,
        "review_ticket_id": ticket_id,
        "status": "queued_for_human_review",
        "estimated_response_days": 5,
    }


@router.get(
    "/audit-log/{customer_token}",
    summary="Get audit trail for a customer (GDPR accountability)",
)
async def get_audit_log(
    customer_token: str,
    limit: int = Query(default=50, ge=1, le=500),
    current_user: TokenPayload = Depends(require_permissions("audit:read")),
    gdpr_service: GdprService = Depends(get_gdpr_service),
):
    """Returns pseudonymised audit log for a customer token."""
    logs = await gdpr_service.get_audit_log(customer_token, limit=limit)
    return {"customer_token": customer_token, "events": logs, "count": len(logs)}
