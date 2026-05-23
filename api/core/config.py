"""
Application Configuration — Production-ready settings with Azure Key Vault support.
All secrets loaded from environment variables / Azure Key Vault.
NEVER hardcode secrets in this file.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, Field, SecretStr, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Centralised application settings.
    Loaded from environment variables (docker/.env or Azure Container Apps secrets).
    Sensitive values are SecretStr — they will not appear in logs or repr().
    """

    # ─── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "AI Churn Analytics Platform"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = Field("production", regex="^(development|staging|production)$")

    # ─── Security ────────────────────────────────────────────────────────────
    SECRET_KEY: SecretStr = Field(..., description="JWT signing secret (min 32 chars)")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALLOWED_ORIGINS: List[str] = ["https://app.churn-analytics.azure.com"]

    # ─── Azure AD ────────────────────────────────────────────────────────────
    AZURE_TENANT_ID: str = Field(..., description="Azure AD tenant ID")
    AZURE_CLIENT_ID: str = Field(..., description="Azure AD app registration client ID")
    AZURE_CLIENT_SECRET: SecretStr = Field(..., description="Azure AD client secret")
    AZURE_AD_AUDIENCE: str = "api://churn-analytics"

    # ─── Azure Key Vault ─────────────────────────────────────────────────────
    AZURE_KEY_VAULT_URL: AnyHttpUrl = Field(
        ..., description="Azure Key Vault URL e.g. https://kv-churn.vault.azure.net/"
    )

    # ─── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: SecretStr = Field(
        ...,
        description="Azure SQL connection string (asyncpg format)",
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # ─── Azure Storage ───────────────────────────────────────────────────────
    AZURE_STORAGE_ACCOUNT: str = Field(..., description="ADLS storage account name")
    AZURE_STORAGE_KEY: SecretStr = Field(..., description="ADLS storage account key")
    AZURE_STORAGE_CONTAINER: str = "churn-analytics"

    # ─── MLflow / Azure ML ───────────────────────────────────────────────────
    MLFLOW_TRACKING_URI: str = Field(
        ..., description="MLflow tracking URI (Azure ML workspace)"
    )
    CHURN_MODEL_NAME: str = "churn-prediction-ensemble"
    CHURN_MODEL_STAGE: str = "Production"
    SEGMENTATION_MODEL_NAME: str = "customer-segmentation-kmeans"
    ANOMALY_MODEL_NAME: str = "anomaly-isolation-forest"
    MODEL_CACHE_TTL_SECONDS: int = 3600  # Reload models from registry every hour

    # ─── Azure OpenAI (GenAI) ────────────────────────────────────────────────
    AZURE_OPENAI_ENDPOINT: AnyHttpUrl = Field(
        ..., description="Azure OpenAI endpoint URL"
    )
    AZURE_OPENAI_API_KEY: SecretStr = Field(..., description="Azure OpenAI API key")
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.2

    # ─── Azure Cognitive Search (RAG) ────────────────────────────────────────
    AZURE_SEARCH_ENDPOINT: AnyHttpUrl = Field(
        ..., description="Azure Cognitive Search endpoint"
    )
    AZURE_SEARCH_KEY: SecretStr = Field(..., description="Azure Cognitive Search admin key")
    AZURE_SEARCH_INDEX: str = "churn-knowledge-base"

    # ─── Redis Cache ─────────────────────────────────────────────────────────
    REDIS_URL: SecretStr = Field(
        ..., description="Azure Cache for Redis connection string"
    )
    PREDICTION_CACHE_TTL: int = 3600  # 1 hour

    # ─── GDPR / Compliance ───────────────────────────────────────────────────
    PII_MASKING_SALT: SecretStr = Field(
        ..., description="Salt for PII HMAC tokenization (from Key Vault)"
    )
    DATA_RETENTION_DAYS: int = 1095  # 3 years default
    GDPR_AUDIT_LOG_RETENTION_DAYS: int = 1095  # 3 years
    DPO_EMAIL: str = "dpo@churn-analytics.example.com"
    GDPR_NOTIFICATION_EMAIL: str = "gdpr-notifications@churn-analytics.example.com"

    # ─── Monitoring ──────────────────────────────────────────────────────────
    APP_INSIGHTS_CONNECTION_STRING: Optional[SecretStr] = None
    LOG_LEVEL: str = Field("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    ENABLE_AUDIT_LOG: bool = True

    # ─── Rate Limiting ───────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Secrets will not appear in logs
        secrets_dir = "/run/secrets"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Use dependency injection: Depends(get_settings) in FastAPI routes.
    """
    return Settings()


# ─── RBAC Role Definitions ───────────────────────────────────────────────────

ROLES = {
    "platform-admin": {
        "description": "Full platform administrator",
        "permissions": ["*"],
    },
    "ml-engineer": {
        "description": "ML model access",
        "permissions": [
            "churn:read", "churn:write",
            "segmentation:read", "segmentation:write",
            "anomaly:read", "anomaly:write",
            "insights:read",
        ],
    },
    "api-consumer": {
        "description": "API read access for integrations",
        "permissions": [
            "churn:read",
            "segmentation:read",
            "anomaly:read",
            "retention:read",
            "insights:read",
        ],
    },
    "bi-analyst": {
        "description": "Power BI and aggregated data access",
        "permissions": ["churn:read", "segmentation:read"],
    },
    "gdpr-officer": {
        "description": "Data Protection Officer access",
        "permissions": ["gdpr:*", "audit:read"],
    },
    "auditor": {
        "description": "Read-only audit log access",
        "permissions": ["audit:read"],
    },
}
