"""
Test fixtures and configuration for pytest.
Uses FastAPI TestClient with mocked Azure services.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

# Set test environment BEFORE importing app
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars-long-here")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("AZURE_TENANT_ID", "test-tenant-id")
os.environ.setdefault("AZURE_CLIENT_ID", "test-client-id")
os.environ.setdefault("AZURE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("AZURE_KEY_VAULT_URL", "https://test.vault.azure.net/")
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
os.environ.setdefault("AZURE_OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("PII_MASKING_SALT", "test-pii-salt-32-chars-minimum!!!")
os.environ.setdefault("AZURE_STORAGE_ACCOUNT", "teststorage")
os.environ.setdefault("AZURE_STORAGE_KEY", "test-storage-key")
os.environ.setdefault("MLFLOW_TRACKING_URI", "http://localhost:5000")
os.environ.setdefault("AZURE_SEARCH_ENDPOINT", "https://test.search.windows.net")
os.environ.setdefault("AZURE_SEARCH_KEY", "test-search-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from api.main import app
from api.core.security import create_access_token


def make_token(roles=None):
    """Create a test JWT token with specified roles."""
    return create_access_token(
        subject="test-user-001",
        roles=roles or ["api-consumer"],
    )


@pytest.fixture
def auth_headers():
    """Standard API consumer auth headers."""
    token = make_token(["api-consumer"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    """Platform admin auth headers."""
    token = make_token(["platform-admin"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def gdpr_headers():
    """GDPR officer auth headers."""
    token = make_token(["gdpr-officer"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ml_headers():
    """ML engineer auth headers."""
    token = make_token(["ml-engineer"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def async_client():
    """Async test client for FastAPI."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def sample_customer():
    """Valid sample customer request payload."""
    return {
        "customer_token": "abc123def456ghi789",
        "tenure_months": 18,
        "monthly_charge_eur": 45.99,
        "total_charges_eur": 827.82,
        "num_products": 2,
        "contract_type": "annual",
        "payment_method": "auto_debit",
        "has_internet_service": True,
        "has_phone_service": True,
        "support_tickets_6m": 2,
        "avg_monthly_usage_gb": 120.5,
        "days_since_last_contact": 45,
        "nps_score": 7.5,
        "payment_delay_count_12m": 0,
    }


@pytest.fixture
def high_risk_customer():
    """High churn risk customer payload."""
    return {
        "customer_token": "risk123token456high789",
        "tenure_months": 3,
        "monthly_charge_eur": 89.99,
        "total_charges_eur": 269.97,
        "num_products": 1,
        "contract_type": "monthly",
        "payment_method": "invoice",
        "has_internet_service": True,
        "has_phone_service": False,
        "support_tickets_6m": 8,
        "avg_monthly_usage_gb": 5.0,
        "days_since_last_contact": 180,
        "nps_score": 2.0,
        "payment_delay_count_12m": 3,
    }


@pytest.fixture
def mock_churn_service():
    """Mock churn service that returns deterministic predictions."""
    from api.routers.churn import ChurnPredictionResponse
    from datetime import datetime, timezone

    mock = AsyncMock()
    mock.predict_single.return_value = ChurnPredictionResponse(
        prediction_id="test-pred-001",
        customer_token="abc123def456ghi789",
        churn_probability=0.72,
        churn_label=True,
        risk_level="HIGH",
        confidence_score=0.84,
        top_churn_drivers=[
            {"feature": "tenure_months", "shap_value": -0.45, "direction": "decreases_churn", "human_label": "Customer tenure"},
            {"feature": "support_tickets_6m", "shap_value": 0.38, "direction": "increases_churn", "human_label": "Support tickets (6m)"},
        ],
        model_version="1.3",
        model_name="churn-prediction-ensemble",
        prediction_timestamp=datetime.now(timezone.utc).isoformat(),
        retention_urgency="within_30_days",
        requires_human_review=False,
    )
    return mock
