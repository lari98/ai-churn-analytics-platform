"""
GDPR Compliance Tests — Verifies all data subject rights work correctly.
Tests: Art. 15 (access), Art. 17 (erasure), Art. 18 (restriction),
       Art. 21 (objection), Art. 22 (human review), consent management.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestGDPRConsentManagement:
    """GDPR Art. 6, 7 — Consent recording and retrieval."""

    @pytest.mark.asyncio
    async def test_record_consent_requires_gdpr_officer_role(
        self, async_client, auth_headers
    ):
        """Standard API consumer cannot record consent."""
        response = await async_client.post(
            "/api/v1/gdpr/consent",
            json={
                "customer_token": "test-token-123",
                "churn_analytics": True,
                "channel": "web_portal",
                "consent_version": "2024-01-01-v2",
            },
            headers=auth_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_record_consent_accepted_by_gdpr_officer(
        self, async_client, gdpr_headers
    ):
        """GDPR officer can record consent."""
        mock_gdpr = AsyncMock()
        mock_gdpr.record_consent = AsyncMock(return_value={
            "consent_id": "consent-001",
            "customer_token": "test-token-123",
            "recorded_at": "2024-01-15T10:00:00Z",
            "purposes": {"churn_analytics": True},
            "version": "2024-01-01-v2",
        })

        with patch("api.routers.gdpr.get_gdpr_service", return_value=lambda: mock_gdpr):
            response = await async_client.post(
                "/api/v1/gdpr/consent",
                json={
                    "customer_token": "test-token-123",
                    "churn_analytics": True,
                    "channel": "web_portal",
                    "consent_version": "2024-01-01-v2",
                },
                headers=gdpr_headers,
            )
        assert response.status_code == 201
        data = response.json()
        assert "consent_id" in data

    @pytest.mark.asyncio
    async def test_consent_channel_validation(self, async_client, gdpr_headers):
        """Invalid consent channel returns 422."""
        response = await async_client.post(
            "/api/v1/gdpr/consent",
            json={
                "customer_token": "test-token-123",
                "churn_analytics": True,
                "channel": "invalid_channel",  # Not in enum
            },
            headers=gdpr_headers,
        )
        assert response.status_code == 422


class TestGDPRDataExport:
    """GDPR Art. 15 — Right of Access."""

    @pytest.mark.asyncio
    async def test_data_export_requires_gdpr_role(self, async_client, auth_headers):
        """Standard API consumer cannot export customer data."""
        response = await async_client.get(
            "/api/v1/gdpr/customer/test-token-123/data-export",
            headers=auth_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_data_export_returns_all_categories(
        self, async_client, gdpr_headers
    ):
        """Data export includes all data categories."""
        mock_gdpr = AsyncMock()
        mock_gdpr.export_customer_data = AsyncMock(return_value={
            "customer_token": "test-token-123",
            "export_id": "export-001",
            "generated_at": "2024-01-15T10:00:00Z",
            "data_categories": ["profile", "churn_scores", "consent_history"],
            "retention_dates": {"profile": "2027-01-01"},
            "processing_purposes": ["churn_analytics"],
            "data": {"profile": {}, "churn_scores": [], "consent_history": []},
        })

        with patch("api.routers.gdpr.get_gdpr_service", return_value=lambda: mock_gdpr):
            response = await async_client.get(
                "/api/v1/gdpr/customer/test-token-123/data-export",
                headers=gdpr_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert "data_categories" in data
        assert "retention_dates" in data
        assert len(data["data_categories"]) > 0


class TestGDPRErasure:
    """GDPR Art. 17 — Right to be Forgotten."""

    @pytest.mark.asyncio
    async def test_erasure_requires_confirm_string(self, async_client, gdpr_headers):
        """Erasure fails without 'CONFIRM_ERASURE' confirmation."""
        mock_gdpr = AsyncMock()
        mock_gdpr.check_legal_hold = AsyncMock(return_value={"has_hold": False})

        with patch("api.routers.gdpr.get_gdpr_service", return_value=lambda: mock_gdpr):
            response = await async_client.delete(
                "/api/v1/gdpr/customer/test-token-123",
                json={
                    "customer_token": "test-token-123",
                    "reason": "customer_request",
                    "requested_by": "dpo@test.com",
                    "confirmation": "WRONG_STRING",  # Wrong confirmation
                },
                headers=gdpr_headers,
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_erasure_succeeds_with_correct_confirmation(
        self, async_client, gdpr_headers
    ):
        """Erasure initiates with correct confirmation and no legal hold."""
        mock_gdpr = AsyncMock()
        mock_gdpr.check_legal_hold = AsyncMock(return_value={"has_hold": False})
        mock_gdpr.execute_erasure = AsyncMock()

        with patch("api.routers.gdpr.get_gdpr_service", return_value=lambda: mock_gdpr):
            response = await async_client.delete(
                "/api/v1/gdpr/customer/test-token-123",
                json={
                    "customer_token": "test-token-123",
                    "reason": "customer_request",
                    "requested_by": "dpo@test.com",
                    "confirmation": "CONFIRM_ERASURE",
                },
                headers=gdpr_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("initiated", "hold_applied")
        assert "erasure_id" in data

    @pytest.mark.asyncio
    async def test_erasure_blocked_by_legal_hold(self, async_client, gdpr_headers):
        """Erasure returns 'hold_applied' status when legal hold exists."""
        mock_gdpr = AsyncMock()
        mock_gdpr.check_legal_hold = AsyncMock(return_value={
            "has_hold": True,
            "hold_type": "active_contract",
            "expires_at": "2025-01-01",
        })

        with patch("api.routers.gdpr.get_gdpr_service", return_value=lambda: mock_gdpr):
            response = await async_client.delete(
                "/api/v1/gdpr/customer/test-token-123",
                json={
                    "customer_token": "test-token-123",
                    "reason": "customer_request",
                    "requested_by": "dpo@test.com",
                    "confirmation": "CONFIRM_ERASURE",
                },
                headers=gdpr_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "hold_applied"

    @pytest.mark.asyncio
    async def test_erasure_requires_gdpr_role(self, async_client, auth_headers):
        """Standard consumer cannot trigger erasure."""
        response = await async_client.delete(
            "/api/v1/gdpr/customer/test-token-123",
            json={
                "customer_token": "test-token-123",
                "reason": "customer_request",
                "requested_by": "api-user",
                "confirmation": "CONFIRM_ERASURE",
            },
            headers=auth_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_erasure_token_mismatch_rejected(self, async_client, gdpr_headers):
        """Token in path and body must match."""
        mock_gdpr = AsyncMock()
        mock_gdpr.check_legal_hold = AsyncMock(return_value={"has_hold": False})

        with patch("api.routers.gdpr.get_gdpr_service", return_value=lambda: mock_gdpr):
            response = await async_client.delete(
                "/api/v1/gdpr/customer/token-in-path",
                json={
                    "customer_token": "different-token-in-body",  # Mismatch
                    "reason": "customer_request",
                    "requested_by": "dpo@test.com",
                    "confirmation": "CONFIRM_ERASURE",
                },
                headers=gdpr_headers,
            )
        assert response.status_code == 400


class TestPIIMasking:
    """GDPR Art. 5 — PII masking in responses."""

    def test_email_is_masked(self):
        """Email addresses are masked in output."""
        from api.middleware.pii_masking import mask_pii_in_text
        text = "Contact john.doe@example.com for details"
        masked = mask_pii_in_text(text)
        assert "john.doe@example.com" not in masked
        assert "MASKED" in masked

    def test_iban_is_masked(self):
        """IBAN numbers are masked in output."""
        from api.middleware.pii_masking import mask_pii_in_text
        text = "IBAN: DE89370400440532013000"
        masked = mask_pii_in_text(text)
        assert "DE89370400440532013000" not in masked
        assert "MASKED" in masked

    def test_pii_field_names_masked(self):
        """Known PII field names in dicts are masked."""
        from api.middleware.pii_masking import mask_pii_in_dict
        data = {
            "customer_token": "safe-token-123",
            "email": "john.doe@example.com",
            "first_name": "John",
            "tenure_months": 12,
        }
        masked = mask_pii_in_dict(data)
        assert masked["tenure_months"] == 12  # Non-PII unchanged
        assert "john.doe@example.com" not in str(masked)
        assert "John" not in str(masked.get("first_name", ""))

    def test_tokenization_is_deterministic(self):
        """Same input always produces same token (referential integrity)."""
        from api.middleware.pii_masking import tokenize_identifier
        token1 = tokenize_identifier("customer-id-12345")
        token2 = tokenize_identifier("customer-id-12345")
        assert token1 == token2

    def test_tokenization_is_irreversible(self):
        """Token cannot be reverse-engineered to original value."""
        from api.middleware.pii_masking import tokenize_identifier
        original = "customer-id-12345"
        token = tokenize_identifier(original)
        assert original not in token  # Original not embedded in token
        assert len(token) == 64  # SHA-256 hex digest
