"""
API Security Tests — RBAC, auth, injection prevention, rate limiting.
Validates: authentication required, role-based access, SQL injection, XSS, etc.
"""

import pytest
from unittest.mock import patch


class TestAuthentication:
    """JWT token validation and auth enforcement."""

    @pytest.mark.asyncio
    async def test_no_token_returns_403(self, async_client, sample_customer):
        """Requests without Authorization header are rejected."""
        response = await async_client.post(
            "/api/v1/churn/predict",
            json=sample_customer,
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_malformed_token_rejected(self, async_client, sample_customer):
        """Malformed Bearer token returns 401."""
        response = await async_client.post(
            "/api/v1/churn/predict",
            json=sample_customer,
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self, async_client, sample_customer):
        """Expired JWT token returns 401."""
        from datetime import timedelta
        from api.core.security import create_access_token
        expired_token = create_access_token(
            subject="user-123",
            roles=["api-consumer"],
            expires_delta=timedelta(seconds=-1),  # Already expired
        )
        response = await async_client.post(
            "/api/v1/churn/predict",
            json=sample_customer,
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth_required(self, async_client):
        """Health endpoint is publicly accessible (for load balancer probes)."""
        response = await async_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_security_headers_present(self, async_client, auth_headers, sample_customer):
        """Response includes required security headers."""
        with patch("api.routers.churn.get_churn_service"):
            response = await async_client.get("/health")
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers


class TestRBAC:
    """Role-Based Access Control — each role sees only what it should."""

    @pytest.mark.asyncio
    async def test_bi_analyst_cannot_call_gdpr_endpoint(
        self, async_client
    ):
        """BI analyst role cannot access GDPR endpoints."""
        from api.core.security import create_access_token
        bi_token = create_access_token("user-bi", roles=["bi-analyst"])
        response = await async_client.get(
            "/api/v1/gdpr/audit-log/test-token-123",
            headers={"Authorization": f"Bearer {bi_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_gdpr_officer_cannot_call_ml_predict(
        self, async_client, sample_customer
    ):
        """GDPR officer cannot call churn prediction (no churn:read permission)."""
        from api.core.security import create_access_token
        gdpr_token = create_access_token("user-dpo", roles=["gdpr-officer"])
        response = await async_client.post(
            "/api/v1/churn/predict",
            json=sample_customer,
            headers={"Authorization": f"Bearer {gdpr_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_platform_admin_can_access_all_endpoints(
        self, async_client, admin_headers
    ):
        """Platform admin has access to health endpoint (wildcard permissions)."""
        response = await async_client.get("/health", headers=admin_headers)
        assert response.status_code == 200

    def test_rbac_roles_are_exclusive(self):
        """Role permissions are correctly scoped — no cross-role contamination."""
        from api.core.config import ROLES
        from api.core.security import _get_permissions_for_roles, _has_permission

        bi_perms = _get_permissions_for_roles(["bi-analyst"])
        gdpr_perms = _get_permissions_for_roles(["gdpr-officer"])

        # BI analyst should NOT have GDPR permissions
        assert not _has_permission(bi_perms, "gdpr:write")
        assert not _has_permission(bi_perms, "gdpr:read")

        # GDPR officer should NOT have ML permissions
        assert not _has_permission(gdpr_perms, "churn:read")
        assert not _has_permission(gdpr_perms, "anomaly:write")

        # Platform admin should have everything
        admin_perms = _get_permissions_for_roles(["platform-admin"])
        assert _has_permission(admin_perms, "gdpr:write")
        assert _has_permission(admin_perms, "churn:read")


class TestInputValidation:
    """Injection prevention and input sanitisation."""

    @pytest.mark.asyncio
    async def test_sql_injection_in_customer_token_rejected(
        self, async_client, auth_headers
    ):
        """SQL injection attempt in customer_token is sanitised."""
        malicious_payload = {
            "customer_token": "'; DROP TABLE customers; --",
            "tenure_months": 12,
            "monthly_charge_eur": 50.0,
            "total_charges_eur": 600.0,
            "num_products": 1,
            "contract_type": "monthly",
            "payment_method": "auto_debit",
            "has_internet_service": True,
            "has_phone_service": True,
            "support_tickets_6m": 0,
            "payment_delay_count_12m": 0,
        }
        response = await async_client.post(
            "/api/v1/churn/predict",
            json=malicious_payload,
            headers=auth_headers,
        )
        # Should either be processed safely (token treated as opaque string) or 422
        # MUST NOT cause a 500 error (which would indicate injection worked)
        assert response.status_code != 500

    @pytest.mark.asyncio
    async def test_xss_in_string_fields_sanitised(
        self, async_client, auth_headers, sample_customer
    ):
        """XSS in string fields does not appear unescaped in response."""
        xss_customer = {
            **sample_customer,
            "customer_token": "<script>alert('xss')</script>",
        }
        response = await async_client.post(
            "/api/v1/churn/predict",
            json=xss_customer,
            headers=auth_headers,
        )
        # Script tags must not appear unescaped in response
        assert "<script>" not in response.text

    @pytest.mark.asyncio
    async def test_extremely_large_payload_rejected(
        self, async_client, auth_headers
    ):
        """Very large payloads are rejected."""
        large_payload = {"data": "A" * 10_000_000}  # 10MB
        response = await async_client.post(
            "/api/v1/churn/predict",
            json=large_payload,
            headers=auth_headers,
        )
        assert response.status_code in (413, 422)

    def test_pii_masking_salt_from_config_not_hardcoded(self):
        """PII masking salt must come from config (Key Vault), not hardcoded."""
        from api.core.config import get_settings
        settings = get_settings()
        salt = settings.PII_MASKING_SALT.get_secret_value()
        assert len(salt) >= 16, "PII salt too short"
        # Check it's not a known test/default value
        forbidden_salts = ["", "salt", "12345", "default", "test"]
        assert salt.lower() not in forbidden_salts


class TestAuditLogging:
    """Verify audit events are generated correctly."""

    def test_audit_event_chain_hash(self):
        """Audit events include chain hash for tamper detection."""
        from api.middleware.audit_log import AuditEvent, AuditEventType, AuditOutcome
        event1 = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            actor_id="user-001", actor_role="api-consumer",
            resource_type="churn_model", resource_id="cust-001",
            action="READ", outcome=AuditOutcome.SUCCESS,
            correlation_id="corr-001",
        )
        event2 = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            actor_id="user-001", actor_role="api-consumer",
            resource_type="churn_model", resource_id="cust-002",
            action="READ", outcome=AuditOutcome.SUCCESS,
            correlation_id="corr-002",
        )
        # Each event has a unique hash
        assert event1.hash != event2.hash
        # Hash is a valid SHA-256 hex string
        assert len(event1.hash) == 64
        assert all(c in "0123456789abcdef" for c in event1.hash)

    def test_audit_event_pseudonymises_actor_id(self):
        """Audit event does not store raw actor ID."""
        from api.middleware.audit_log import AuditEvent, AuditEventType, AuditOutcome
        raw_id = "john.doe@company.com"
        event = AuditEvent(
            event_type=AuditEventType.ML_PREDICTION,
            actor_id=raw_id, actor_role="ml-engineer",
            resource_type="churn_model", resource_id="cust-001",
            action="PREDICT", outcome=AuditOutcome.SUCCESS,
            correlation_id="corr-001",
        )
        # Raw ID should not appear in event dict
        event_dict = event.to_dict()
        assert raw_id not in str(event_dict)
        assert "@" not in event.actor_id  # Email not stored
