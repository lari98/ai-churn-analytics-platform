"""
Churn API Tests — ML accuracy, API contract, edge cases, batch processing.
Coverage target: ≥ 85% of churn router and service code.
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


class TestChurnPredictEndpoint:
    """Tests for POST /api/v1/churn/predict"""

    @pytest.mark.asyncio
    async def test_predict_returns_200_with_valid_payload(
        self, async_client, auth_headers, sample_customer, mock_churn_service
    ):
        """Valid customer payload returns 200 with churn prediction."""
        with patch("api.routers.churn.get_churn_service", return_value=lambda: mock_churn_service), \
             patch("api.routers.churn.get_gdpr_service", return_value=lambda: AsyncMock(check_processing_consent=AsyncMock())):
            response = await async_client.post(
                "/api/v1/churn/predict",
                json=sample_customer,
                headers=auth_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert "churn_probability" in data
        assert 0.0 <= data["churn_probability"] <= 1.0
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert "top_churn_drivers" in data
        assert "prediction_id" in data

    @pytest.mark.asyncio
    async def test_predict_requires_auth(self, async_client, sample_customer):
        """Unauthenticated requests return 403 or 401."""
        response = await async_client.post(
            "/api/v1/churn/predict",
            json=sample_customer,
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_predict_validates_tenure_negative(self, async_client, auth_headers, sample_customer):
        """Negative tenure should return 422 validation error."""
        bad_customer = {**sample_customer, "tenure_months": -1}
        response = await async_client.post(
            "/api/v1/churn/predict",
            json=bad_customer,
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_predict_validates_contract_type(self, async_client, auth_headers, sample_customer):
        """Invalid contract type returns 422."""
        bad_customer = {**sample_customer, "contract_type": "biweekly"}
        response = await async_client.post(
            "/api/v1/churn/predict",
            json=bad_customer,
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_predict_high_risk_flags_human_review(
        self, async_client, auth_headers, high_risk_customer, mock_churn_service
    ):
        """Very high churn probability should set requires_human_review=True."""
        from datetime import datetime, timezone
        from api.routers.churn import ChurnPredictionResponse

        mock_churn_service.predict_single.return_value = ChurnPredictionResponse(
            prediction_id="test-pred-002",
            customer_token=high_risk_customer["customer_token"],
            churn_probability=0.92,
            churn_label=True,
            risk_level="CRITICAL",
            confidence_score=0.95,
            top_churn_drivers=[],
            model_version="1.3",
            model_name="churn-prediction-ensemble",
            prediction_timestamp=datetime.now(timezone.utc).isoformat(),
            retention_urgency="immediate",
            requires_human_review=True,
        )

        with patch("api.routers.churn.get_churn_service", return_value=lambda: mock_churn_service), \
             patch("api.routers.churn.get_gdpr_service", return_value=lambda: AsyncMock(check_processing_consent=AsyncMock())):
            response = await async_client.post(
                "/api/v1/churn/predict",
                json=high_risk_customer,
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["requires_human_review"] is True
        assert data["risk_level"] == "CRITICAL"

    @pytest.mark.asyncio
    async def test_predict_missing_required_fields(self, async_client, auth_headers):
        """Missing required fields return 422."""
        response = await async_client.post(
            "/api/v1/churn/predict",
            json={"tenure_months": 12},  # missing most required fields
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_predict_response_no_raw_pii(
        self, async_client, auth_headers, sample_customer, mock_churn_service
    ):
        """Response must not contain raw PII (name, email, phone, IBAN)."""
        with patch("api.routers.churn.get_churn_service", return_value=lambda: mock_churn_service), \
             patch("api.routers.churn.get_gdpr_service", return_value=lambda: AsyncMock(check_processing_consent=AsyncMock())):
            response = await async_client.post(
                "/api/v1/churn/predict",
                json=sample_customer,
                headers=auth_headers,
            )
        assert response.status_code == 200
        response_text = response.text
        # Ensure no raw PII patterns in response
        import re
        assert not re.search(r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b', response_text), \
            "Email found in response"
        assert not re.search(r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b', response_text), \
            "IBAN found in response"

    @pytest.mark.asyncio
    async def test_batch_predict_accepts_multiple_customers(
        self, async_client, auth_headers, sample_customer, mock_churn_service
    ):
        """Batch endpoint accepts list of customers."""
        mock_churn_service.predict_batch = AsyncMock(return_value=[])

        with patch("api.routers.churn.get_churn_service", return_value=lambda: mock_churn_service):
            response = await async_client.post(
                "/api/v1/churn/batch-predict",
                json={"customers": [sample_customer] * 3, "async_processing": False},
                headers=auth_headers,
            )
        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_batch_predict_rejects_over_1000(
        self, async_client, auth_headers, sample_customer
    ):
        """Batch endpoint rejects more than 1000 customers."""
        response = await async_client.post(
            "/api/v1/churn/batch-predict",
            json={"customers": [sample_customer] * 1001},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_model_info_endpoint(self, async_client, auth_headers, mock_churn_service):
        """Model info endpoint returns model metadata."""
        mock_churn_service.get_model_info = AsyncMock(return_value={
            "name": "churn-prediction-ensemble",
            "version": "1.3",
            "auc_roc": 0.872,
        })
        with patch("api.routers.churn.get_churn_service", return_value=lambda: mock_churn_service):
            response = await async_client.get(
                "/api/v1/churn/model-info",
                headers=auth_headers,
            )
        assert response.status_code == 200


class TestChurnMLAccuracy:
    """ML model accuracy validation tests."""

    def test_risk_level_thresholds(self):
        """Risk level assignment follows defined thresholds."""
        from api.services.churn_service import _get_risk_level
        assert _get_risk_level(0.10) == "LOW"
        assert _get_risk_level(0.30) == "MEDIUM"
        assert _get_risk_level(0.55) == "HIGH"
        assert _get_risk_level(0.75) == "CRITICAL"
        assert _get_risk_level(1.0) == "CRITICAL"
        assert _get_risk_level(0.0) == "LOW"

    def test_retention_urgency_mapping(self):
        """Retention urgency maps correctly to churn probability."""
        from api.services.churn_service import _get_retention_urgency
        assert _get_retention_urgency(0.80) == "immediate"
        assert _get_retention_urgency(0.60) == "within_30_days"
        assert _get_retention_urgency(0.30) == "monitor"

    def test_feature_encoding_contract_types(self):
        """All contract types encode to valid integers."""
        import numpy as np
        from api.services.churn_service import ChurnService
        from api.routers.churn import ChurnPredictionRequest

        service = ChurnService()
        for contract in ["monthly", "annual", "two_year"]:
            req = ChurnPredictionRequest(
                customer_token="test-token-abc123",
                tenure_months=12,
                monthly_charge_eur=50.0,
                total_charges_eur=600.0,
                num_products=2,
                contract_type=contract,
                payment_method="auto_debit",
                has_internet_service=True,
                has_phone_service=True,
                support_tickets_6m=0,
                payment_delay_count_12m=0,
            )
            features = service._request_to_features(req)
            assert features.shape == (1, 13), f"Unexpected shape for contract_type={contract}"
            assert not np.any(np.isnan(features)), "NaN in feature vector"
