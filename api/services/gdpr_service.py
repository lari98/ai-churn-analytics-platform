"""
GDPR Service — Implements all data subject rights operations.
Coordinates erasure across Azure SQL, ADLS, Redis, Cosmos DB, and ML feature store.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException, status

from api.core.config import get_settings
from api.middleware.audit_log import log_gdpr_event, AuditEventType, AuditOutcome

logger = logging.getLogger(__name__)
settings = get_settings()


class ConsentNotGrantedError(Exception):
    """Raised when required consent has not been given."""


class LegalHoldError(Exception):
    """Raised when data is under legal hold and cannot be deleted."""


class GdprService:
    """
    Handles all GDPR operations:
    - Consent management
    - Data export (Art. 15)
    - Erasure (Art. 17)
    - Processing restriction (Art. 18)
    - Objection recording (Art. 21)
    - Human review routing (Art. 22)
    - Audit log queries
    """

    async def check_processing_consent(
        self, customer_token: str, purpose: str
    ) -> bool:
        """
        Gate: check if customer consented to this processing purpose.
        Raises ConsentNotGrantedError if not consented.
        All ML/analytics endpoints must call this.
        """
        consent = await self.get_consent(customer_token)

        if consent is None:
            # No consent record → deny processing
            raise HTTPException(
                status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                detail=f"No consent record for customer. Cannot process for purpose: {purpose}",
            )

        # Check specific purpose
        purposes = consent.get("purposes", {})
        if not purposes.get(purpose, False):
            raise HTTPException(
                status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                detail=f"Customer has not consented to processing purpose: {purpose}",
            )

        # Check processing restriction flag
        if purposes.get("processing_restricted", False):
            raise HTTPException(
                status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                detail="Customer has requested processing restriction (GDPR Art. 18)",
            )

        return True

    async def record_consent(
        self, consent_record, actor_id: str
    ) -> dict:
        """Store consent record in Azure SQL. Immutable — creates new version."""
        consent_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # In production: INSERT INTO gdpr_consent (customer_token, purposes, ...) VALUES (...)
        record = {
            "consent_id": consent_id,
            "customer_token": consent_record.customer_token,
            "recorded_at": now,
            "purposes": {
                "churn_analytics": consent_record.churn_analytics,
                "behavioral_profiling": consent_record.behavioral_profiling,
                "marketing_contact": consent_record.marketing_contact,
                "data_sharing_third_parties": consent_record.data_sharing_third_parties,
                "genai_processing": consent_record.genai_processing,
            },
            "version": consent_record.consent_version,
            "channel": consent_record.channel,
            "recorded_by": actor_id,
        }
        logger.info("Consent recorded for token %s...", consent_record.customer_token[:8])
        return record

    async def get_consent(self, customer_token: str) -> Optional[dict]:
        """Retrieve latest consent record from Azure SQL."""
        # In production: SELECT * FROM gdpr_consent WHERE customer_token = ? ORDER BY recorded_at DESC LIMIT 1
        # Mock: return a default consent for demonstration
        return {
            "consent_id": str(uuid4()),
            "customer_token": customer_token,
            "recorded_at": "2024-01-01T00:00:00Z",
            "purposes": {
                "churn_analytics": True,
                "behavioral_profiling": True,
                "marketing_contact": False,
                "genai_processing": True,
                "processing_restricted": False,
            },
            "version": "2024-01-01-v2",
        }

    async def export_customer_data(
        self, customer_token: str, format: str = "json"
    ) -> dict:
        """
        GDPR Art. 15 — Export all personal data held for customer.
        Aggregates from: Azure SQL, ADLS metadata, Cosmos DB, churn scores.
        """
        export_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # In production: query all systems in parallel
        data = {
            "profile": {
                "customer_token": customer_token,
                "status": "active",
                "created_at": "2022-03-15T00:00:00Z",
            },
            "churn_scores": [
                {"date": "2024-01-01", "probability": 0.45, "risk_level": "MEDIUM"},
            ],
            "consent_history": [
                {"date": "2024-01-01", "version": "v2", "channel": "web_portal"},
            ],
            "processing_log": [
                {"purpose": "churn_analytics", "date": "2024-01-15", "legal_basis": "consent"},
            ],
        }

        return {
            "customer_token": customer_token,
            "export_id": export_id,
            "generated_at": now,
            "data_categories": list(data.keys()),
            "retention_dates": {
                "profile": "2027-01-01",
                "churn_scores": "2025-01-01",
                "audit_logs": "2027-01-01",
            },
            "processing_purposes": ["churn_analytics", "fraud_prevention"],
            "data": data,
        }

    async def check_legal_hold(self, customer_token: str) -> dict:
        """
        Check if customer data is under legal hold before erasure.
        Legal holds from: active contracts, pending disputes, regulatory requirements.
        """
        # In production: query legal_holds table
        return {"has_hold": False, "hold_type": None, "expires_at": None}

    async def execute_erasure(
        self,
        erasure_id: str,
        customer_token: str,
        reason: str,
        requested_by: str,
        actor_id: str,
    ) -> dict:
        """
        GDPR Art. 17 — Execute full data erasure across all systems.
        Called as background task.
        """
        logger.info("Executing GDPR erasure %s for customer %s...", erasure_id, customer_token[:8])
        affected_systems = []

        try:
            # Step 1: Azure SQL deletion
            await self._delete_from_sql(customer_token)
            affected_systems.append("azure_sql")

            # Step 2: ADLS deletion
            await self._delete_from_adls(customer_token)
            affected_systems.append("adls")

            # Step 3: Redis cache purge
            await self._purge_redis_cache(customer_token)
            affected_systems.append("redis_cache")

            # Step 4: Cosmos DB deletion
            await self._delete_from_cosmos(customer_token)
            affected_systems.append("cosmos_db")

            # Step 5: ML Feature Store exclusion
            await self._exclude_from_feature_store(customer_token)
            affected_systems.append("ml_feature_store")

            # Step 6: Pseudonymise audit logs (CANNOT delete — legal obligation)
            # Audit logs are retained but customer_token is replaced with erasure_id
            await self._pseudonymise_audit_logs(customer_token, erasure_id)
            affected_systems.append("audit_logs_pseudonymised")

            logger.info("GDPR erasure %s completed. Systems affected: %s", erasure_id, affected_systems)

            log_gdpr_event(
                event_type=AuditEventType.GDPR_ERASURE,
                customer_token=erasure_id,  # Use erasure_id as token post-erasure
                actor_id=actor_id,
                actor_role="gdpr-officer",
                outcome=AuditOutcome.SUCCESS,
                gdpr_basis="data_subject_request",
                correlation_id=erasure_id,
                metadata={"reason": reason, "systems": affected_systems},
            )

        except Exception as exc:
            logger.error("GDPR erasure %s failed: %s", erasure_id, exc)

        return {"erasure_id": erasure_id, "systems_affected": affected_systems}

    async def restrict_processing(self, customer_token: str, reason: str) -> None:
        """Flag customer record to exclude from all processing."""
        # In production: UPDATE customers SET processing_restricted = TRUE WHERE token = ?
        logger.info("Processing restricted for customer %s...", customer_token[:8])

    async def record_objection(
        self, customer_token: str, purposes: List[str], reason: str
    ) -> None:
        """Record processing objection for specific purposes."""
        # In production: INSERT INTO processing_objections
        logger.info("Objection recorded for customer %s, purposes: %s", customer_token[:8], purposes)

    async def create_human_review_ticket(
        self, customer_token: str, reason: str
    ) -> str:
        """Create ticket in human review queue (Azure Service Bus message)."""
        ticket_id = str(uuid4())
        # In production: send message to Azure Service Bus human-review queue
        logger.info("Human review ticket %s created for customer %s...", ticket_id, customer_token[:8])
        return ticket_id

    async def get_audit_log(
        self, customer_token: str, limit: int = 50
    ) -> List[dict]:
        """Query audit log for customer token."""
        # In production: SELECT * FROM audit_log WHERE resource_id_token = ? LIMIT ?
        return []

    # ─── Private helpers (in production: real Azure SDK calls) ───────────────

    async def _delete_from_sql(self, customer_token: str) -> None:
        # DELETE FROM customers, churn_scores, segments WHERE customer_token = ?
        logger.debug("SQL deletion for %s...", customer_token[:8])

    async def _delete_from_adls(self, customer_token: str) -> None:
        # Azure SDK: container_client.delete_blob(f"customers/{customer_token}/**")
        logger.debug("ADLS deletion for %s...", customer_token[:8])

    async def _purge_redis_cache(self, customer_token: str) -> None:
        # redis_client.delete(f"churn:{customer_token}", f"segment:{customer_token}")
        logger.debug("Redis purge for %s...", customer_token[:8])

    async def _delete_from_cosmos(self, customer_token: str) -> None:
        # container.delete_item(item=customer_token, partition_key=customer_token)
        logger.debug("Cosmos DB deletion for %s...", customer_token[:8])

    async def _exclude_from_feature_store(self, customer_token: str) -> None:
        # Mark customer as excluded in ML feature store exclusion list
        logger.debug("Feature store exclusion for %s...", customer_token[:8])

    async def _pseudonymise_audit_logs(
        self, customer_token: str, erasure_id: str
    ) -> None:
        # UPDATE audit_log SET resource_id_token = ? WHERE resource_id_token = ?
        # Replaces customer token with erasure_id (pseudonymisation, not deletion)
        logger.debug("Audit log pseudonymisation: %s → %s...", customer_token[:8], erasure_id[:8])


# ─── Dependency ───────────────────────────────────────────────────────────────
_gdpr_service_instance = GdprService()


def get_gdpr_service() -> GdprService:
    return _gdpr_service_instance
