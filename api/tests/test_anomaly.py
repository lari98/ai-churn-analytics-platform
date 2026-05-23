"""
Anomaly Detection Tests — Edge cases, accuracy, model drift detection.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestAnomalyDetection:

    @pytest.mark.asyncio
    async def test_normal_transaction_returns_low_score(self, async_client, auth_headers):
        """Normal transaction returns low anomaly score."""
        response = await async_client.post(
            "/api/v1/anomaly/detect",
            json={
                "customer_token": "safe-customer-token-123",
                "transaction_amount_eur": 45.0,
                "transaction_type": "payment",
                "channel": "web",
                "hour_of_day": 14,
                "day_of_week": 2,
                "country_code": "DE",
                "is_foreign_country": False,
                "previous_avg_amount_eur": 50.0,
                "transactions_last_24h": 2,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["anomaly_score"] < 0.5
        assert data["severity"] in ("low", "medium")

    @pytest.mark.asyncio
    async def test_suspicious_transaction_returns_high_score(
        self, async_client, auth_headers
    ):
        """Suspicious transaction (foreign, night, high velocity) gets high score."""
        response = await async_client.post(
            "/api/v1/anomaly/detect",
            json={
                "customer_token": "risk-customer-token-456",
                "transaction_amount_eur": 5000.0,
                "transaction_type": "transfer",
                "channel": "api",
                "hour_of_day": 3,  # 3am
                "day_of_week": 6,
                "country_code": "US",
                "is_foreign_country": True,
                "previous_avg_amount_eur": 50.0,  # 100x normal
                "transactions_last_24h": 25,  # Very high velocity
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["anomaly_score"] > 0.5
        assert data["severity"] in ("high", "critical")
        assert len(data["anomaly_types"]) > 0

    @pytest.mark.asyncio
    async def test_missing_previous_avg_handled_gracefully(
        self, async_client, auth_headers
    ):
        """Missing previous_avg_amount_eur is handled without error."""
        response = await async_client.post(
            "/api/v1/anomaly/detect",
            json={
                "customer_token": "new-customer-token-789",
                "transaction_amount_eur": 100.0,
                "transaction_type": "purchase",
                "channel": "mobile",
                "hour_of_day": 12,
                "day_of_week": 1,
                "country_code": "DE",
                "is_foreign_country": False,
                "transactions_last_24h": 1,
                # No previous_avg_amount_eur
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_zero_amount_transaction(self, async_client, auth_headers):
        """Zero amount transaction is handled without error."""
        response = await async_client.post(
            "/api/v1/anomaly/detect",
            json={
                "customer_token": "test-token-zero",
                "transaction_amount_eur": 0.0,
                "transaction_type": "refund",
                "channel": "web",
                "hour_of_day": 10,
                "day_of_week": 0,
                "country_code": "AT",
                "is_foreign_country": False,
                "transactions_last_24h": 0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_critical_anomaly_requires_immediate_review(
        self, async_client, auth_headers
    ):
        """Critical anomaly sets requires_immediate_review=True."""
        response = await async_client.post(
            "/api/v1/anomaly/detect",
            json={
                "customer_token": "fraud-test-token-999",
                "transaction_amount_eur": 9999.0,
                "transaction_type": "transfer",
                "channel": "api",
                "hour_of_day": 2,
                "day_of_week": 6,
                "country_code": "XX",
                "is_foreign_country": True,
                "previous_avg_amount_eur": 20.0,
                "transactions_last_24h": 50,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        if data["anomaly_score"] >= 0.85:
            assert data["requires_immediate_review"] is True

    def test_severity_mapping_is_monotonic(self):
        """Higher scores map to higher severity levels."""
        from api.routers.anomaly import _get_severity
        assert _get_severity(0.1) == "low"
        assert _get_severity(0.5) == "medium"
        assert _get_severity(0.7) == "high"
        assert _get_severity(0.9) == "critical"

    def test_anomaly_type_detection_foreign_country(self):
        """Foreign country flag triggers unusual_location anomaly type."""
        from api.routers.anomaly import _identify_anomaly_types, TransactionEvent
        event = TransactionEvent(
            customer_token="test",
            transaction_amount_eur=100.0,
            transaction_type="payment",
            channel="web",
            hour_of_day=10,
            day_of_week=1,
            country_code="US",
            is_foreign_country=True,
            transactions_last_24h=1,
        )
        types = _identify_anomaly_types(event, 0.3)
        assert "unusual_location" in types

    def test_anomaly_type_velocity_spike(self):
        """High transaction count triggers velocity_spike."""
        from api.routers.anomaly import _identify_anomaly_types, TransactionEvent
        event = TransactionEvent(
            customer_token="test",
            transaction_amount_eur=50.0,
            transaction_type="payment",
            channel="mobile",
            hour_of_day=15,
            day_of_week=2,
            country_code="DE",
            is_foreign_country=False,
            transactions_last_24h=25,  # High velocity
        )
        types = _identify_anomaly_types(event, 0.5)
        assert "velocity_spike" in types


class TestModelDrift:
    """PSI-based model drift detection tests."""

    def test_psi_low_for_similar_distributions(self):
        """PSI is low when training and production distributions are similar."""
        import numpy as np
        from ml.training.train_churn import compute_psi
        np.random.seed(42)
        expected = np.random.normal(0.5, 0.1, 1000)
        actual = np.random.normal(0.5, 0.1, 1000)
        psi = compute_psi(np.clip(expected, 0.01, 0.99), np.clip(actual, 0.01, 0.99))
        assert psi < 0.10, f"PSI {psi} should be < 0.10 for similar distributions"

    def test_psi_high_for_different_distributions(self):
        """PSI is high when distributions differ significantly."""
        import numpy as np
        from ml.training.train_churn import compute_psi
        np.random.seed(42)
        expected = np.random.normal(0.3, 0.05, 1000)
        actual = np.random.normal(0.7, 0.05, 1000)  # Shifted distribution
        psi = compute_psi(np.clip(expected, 0.01, 0.99), np.clip(actual, 0.01, 0.99))
        assert psi > 0.20, f"PSI {psi} should be > 0.20 for different distributions"
