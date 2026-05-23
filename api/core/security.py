"""
Security: JWT Authentication + Azure AD validation + RBAC enforcement.
Implements OAuth2 Bearer token with Azure AD B2C integration.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from api.core.config import ROLES, get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── OAuth2 / Bearer scheme ──────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=True)


# ─── Token Models ────────────────────────────────────────────────────────────

class TokenPayload(BaseModel):
    """Decoded JWT token payload."""
    sub: str                          # Subject (user ID / service principal)
    roles: List[str] = []            # RBAC roles assigned in Azure AD
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    aud: Optional[str] = None
    iss: Optional[str] = None


class TokenResponse(BaseModel):
    """Token issuance response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


# ─── Token Creation (internal service tokens) ────────────────────────────────

def create_access_token(
    subject: str,
    roles: List[str],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a signed JWT access token.
    Used for internal service-to-service auth only.
    External clients must use Azure AD tokens.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: Dict[str, Any] = {
        "sub": subject,
        "roles": roles,
        "iat": now,
        "exp": expire,
        "aud": settings.AZURE_AD_AUDIENCE,
        "iss": f"https://churn-analytics.example.com",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )


# ─── Token Validation ────────────────────────────────────────────────────────

async def validate_azure_ad_token(token: str) -> TokenPayload:
    """
    Validate Azure AD JWT token against Azure AD JWKS endpoint.
    Verifies signature, expiry, audience, and issuer.
    """
    jwks_url = (
        f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}"
        f"/discovery/v2.0/keys"
    )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()

        # Decode and validate
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.AZURE_AD_AUDIENCE,
            issuer=f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/v2.0",
        )

        # Extract roles from Azure AD "roles" claim
        roles = payload.get("roles", [])

        return TokenPayload(
            sub=payload["sub"],
            roles=roles,
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            aud=payload.get("aud"),
            iss=payload.get("iss"),
        )

    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except httpx.HTTPError as exc:
        logger.error("Azure AD JWKS fetch failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


def validate_internal_token(token: str) -> TokenPayload:
    """Validate internally issued JWT (service-to-service)."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
            audience=settings.AZURE_AD_AUDIENCE,
        )
        return TokenPayload(
            sub=payload["sub"],
            roles=payload.get("roles", []),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
    except JWTError as exc:
        logger.warning("Internal JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── FastAPI Dependencies ─────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> TokenPayload:
    """
    FastAPI dependency: validates Bearer token.
    Supports both Azure AD tokens and internal service tokens.
    """
    token = credentials.credentials

    # Try Azure AD validation first, fall back to internal
    try:
        return await validate_azure_ad_token(token)
    except HTTPException:
        # Try internal token (for local dev / service mesh)
        if settings.ENVIRONMENT == "development":
            return validate_internal_token(token)
        raise


def require_permissions(*required_permissions: str):
    """
    FastAPI dependency factory for permission-based access control.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_permissions("gdpr:*"))])

    Args:
        *required_permissions: Permission strings like "churn:read", "gdpr:*"
    """
    async def permission_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        user_permissions = _get_permissions_for_roles(current_user.roles)

        for required in required_permissions:
            if not _has_permission(user_permissions, required):
                logger.warning(
                    "Access denied: user %s lacks permission %s (has roles: %s)",
                    current_user.sub[:8],
                    required,
                    current_user.roles,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {required}",
                )

        return current_user

    return permission_checker


def _get_permissions_for_roles(roles: List[str]) -> List[str]:
    """Expand role names to their permission lists."""
    permissions: List[str] = []
    for role in roles:
        role_def = ROLES.get(role, {})
        permissions.extend(role_def.get("permissions", []))
    return list(set(permissions))


def _has_permission(user_permissions: List[str], required: str) -> bool:
    """
    Check if user has required permission.
    Supports wildcard (*) in both stored and required permissions.
    """
    if "*" in user_permissions:
        return True  # platform-admin

    # Check wildcard patterns (e.g. "gdpr:*" grants "gdpr:read", "gdpr:write")
    required_prefix = required.split(":")[0]
    for perm in user_permissions:
        if perm == required:
            return True
        if perm == f"{required_prefix}:*":
            return True
        if perm == "*":
            return True

    return False
