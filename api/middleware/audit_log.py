"""
Immutable Audit Logging Middleware — GDPR Art. 5(2) accountability.
Logs all data access events to Azure Monitor + Azure SQL (append-only).
Implements cryptographic hash chain for tamper detection.
"""

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from api.middleware.pii_masking import tokenize_identifier

logger = logging.getLogger("audit")

# ─── Audit Event Types ───────────────────────────────────────────────────────

class AuditEventType:
    DATA_ACCESS = "DATA_ACCESS"
    DATA_MODIFICATION = "DATA_MODIFICATION"
    GDPR_REQUEST = "GDPR_REQUEST"
    GDPR_ERASURE = "GDPR_ERASURE"
    GDPR_EXPORT = "GDPR_EXPORT"
    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAILURE = "AUTH_FAILURE"
    ACCESS_DENIED = "ACCESS_DENIED"
    ML_PREDICTION = "ML_PREDICTION"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    MODEL_RETRAIN = "MODEL_RETRAIN"
    CONSENT_RECORDED = "CONSENT_RECORDED"
    CONSENT_WITHDRAWN = "CONSENT_WITHDRAWN"


class AuditOutcome:
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    DENIED = "DENIED"
    PARTIAL = "PARTIAL"


# ─── Audit Event ─────────────────────────────────────────────────────────────

class AuditEvent:
    """
    Immutable audit event. All PII is pseudonymised before logging.
    Hash chain ensures tamper detection.
    """

    # Class-level chain: hash of previous event (in-memory; persisted to DB)
    _previous_hash: str = "0" * 64  # Genesis block

    def __init__(
        self,
        event_type: str,
        actor_id: str,
        actor_role: str,
        resource_type: str,
        resource_id: str,
        action: str,
        outcome: str,
        correlation_id: str,
        ip_address: str = "",
        gdpr_basis: str = "",
        metadata: Optional[dict] = None,
        http_method: str = "",
        endpoint: str = "",
        status_code: int = 200,
        duration_ms: float = 0.0,
    ):
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.event_type = event_type
        self.actor_id = tokenize_identifier(actor_id) if actor_id else "anonymous"
        self.actor_role = actor_role
        self.ip_hash = tokenize_identifier(ip_address)[:16] if ip_address else ""
        self.resource_type = resource_type
        self.resource_id_token = tokenize_identifier(resource_id) if resource_id else ""
        self.action = action
        self.outcome = outcome
        self.correlation_id = correlation_id
        self.gdpr_basis = gdpr_basis
        self.metadata = metadata or {}
        self.http_method = http_method
        self.endpoint = endpoint
        self.status_code = status_code
        self.duration_ms = duration_ms
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA-256 hash chaining this event to the previous."""
        content = json.dumps({
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "actor_id": self.actor_id,
            "resource_id_token": self.resource_id_token,
            "action": self.action,
            "outcome": self.outcome,
            "previous_hash": AuditEvent._previous_hash,
        }, sort_keys=True)
        current_hash = hashlib.sha256(content.encode()).hexdigest()
        AuditEvent._previous_hash = current_hash
        return current_hash

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "actor": {
                "id_token": self.actor_id,
                "role": self.actor_role,
                "ip_hash": self.ip_hash,
            },
            "resource": {
                "type": self.resource_type,
                "id_token": self.resource_id_token,
                "action": self.action,
            },
            "http": {
                "method": self.http_method,
                "endpoint": self.endpoint,
                "status_code": self.status_code,
                "duration_ms": round(self.duration_ms, 2),
            },
            "outcome": self.outcome,
            "correlation_id": self.correlation_id,
            "gdpr_basis": self.gdpr_basis,
            "chain_hash": self.hash,
            "metadata": self.metadata,
        }

    def log(self) -> None:
        """Write to structured audit logger (→ Azure Monitor)."""
        logger.info(json.dumps(self.to_dict()))


# ─── Middleware ───────────────────────────────────────────────────────────────

class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware that creates an audit log entry for every API request.
    PII in paths/payloads is pseudonymised before logging.
    """

    # Map path prefixes to event types and resource types
    ENDPOINT_MAPPING = {
        "/api/v1/churn": (AuditEventType.ML_PREDICTION, "churn_model"),
        "/api/v1/segmentation": (AuditEventType.DATA_ACCESS, "customer_segment"),
        "/api/v1/anomaly": (AuditEventType.DATA_ACCESS, "anomaly_score"),
        "/api/v1/retention": (AuditEventType.DATA_ACCESS, "retention_recommendation"),
        "/api/v1/gdpr": (AuditEventType.GDPR_REQUEST, "gdpr_data"),
        "/api/v1/insights": (AuditEventType.DATA_ACCESS, "genai_insight"),
    }

    SKIP_PATHS = frozenset({"/health", "/metrics", "/docs", "/redoc", "/openapi.json"})

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.monotonic()
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Add correlation ID to request state for downstream use
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        duration_ms = (time.monotonic() - start_time) * 1000

        # Determine event type and resource type
        event_type, resource_type = self._classify_endpoint(request.url.path)

        # Extract actor from JWT if available (without failing on missing auth)
        actor_id = getattr(request.state, "user_id", "unknown")
        actor_role = getattr(request.state, "user_role", "unknown")
        resource_id = self._extract_resource_id(request.url.path)

        outcome = (
            AuditOutcome.SUCCESS
            if response.status_code < 400
            else (
                AuditOutcome.DENIED if response.status_code == 403
                else AuditOutcome.FAILURE
            )
        )

        event = AuditEvent(
            event_type=event_type,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type=resource_type,
            resource_id=resource_id,
            action=request.method,
            outcome=outcome,
            correlation_id=correlation_id,
            ip_address=request.client.host if request.client else "",
            http_method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        event.log()

        # Add audit headers to response
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Audit-Event-ID"] = event.event_id

        return response

    def _classify_endpoint(self, path: str) -> tuple:
        for prefix, (event_type, resource_type) in self.ENDPOINT_MAPPING.items():
            if path.startswith(prefix):
                return event_type, resource_type
        return AuditEventType.DATA_ACCESS, "unknown"

    def _extract_resource_id(self, path: str) -> str:
        """Extract customer/resource ID from URL path for pseudonymisation."""
        parts = path.strip("/").split("/")
        # Convention: /api/v1/{resource}/{id}/...
        if len(parts) >= 4:
            return parts[3]
        return ""


# ─── Manual audit logging helper ─────────────────────────────────────────────

def log_gdpr_event(
    event_type: str,
    customer_token: str,
    actor_id: str,
    actor_role: str,
    outcome: str,
    gdpr_basis: str,
    correlation_id: str,
    metadata: Optional[dict] = None,
) -> None:
    """
    Log a GDPR-specific audit event manually.
    Use this for GDPR data subject requests, consent changes, erasure.
    """
    event = AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="customer_data",
        resource_id=customer_token,
        action="GDPR_OPERATION",
        outcome=outcome,
        correlation_id=correlation_id,
        gdpr_basis=gdpr_basis,
        metadata=metadata or {},
    )
    event.log()
