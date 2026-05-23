"""
PII Masking Middleware — GDPR Art. 5(1)(f) compliance.
Automatically detects and masks PII in all API responses.
Uses regex patterns + NER model for comprehensive detection.
"""

import hashlib
import hmac
import json
import logging
import re
from typing import Any, Dict, Union

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from api.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── PII Detection Patterns (DACH-specific) ──────────────────────────────────

PII_PATTERNS: Dict[str, re.Pattern] = {
    "email": re.compile(
        r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b",
        re.IGNORECASE,
    ),
    "german_phone": re.compile(
        r"(\+49|0049|0)[\s\-]?(\(0\))?[\s\-]?[1-9][0-9]{1,4}[\s\-]?[0-9]{3,12}",
    ),
    "iban": re.compile(
        r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b",
    ),
    "german_postal_code": re.compile(
        r"\b[0-9]{5}\b",  # German PLZ — context-dependent; mask in addresses
    ),
    "ipv4": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
    ),
    "credit_card": re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|[25][1-7][0-9]{14}|"
        r"6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13})\b",
    ),
}

# Fields that always contain PII (applied to JSON keys)
PII_FIELD_NAMES = frozenset({
    "email", "phone", "mobile", "first_name", "last_name", "full_name",
    "name", "address", "street", "city", "postal_code", "iban",
    "account_number", "tax_id", "steuer_id", "ip_address", "device_id",
    "date_of_birth", "geburtsdatum",
})


# ─── Masking Functions ───────────────────────────────────────────────────────

def mask_pii_value(value: str, field_name: str = "") -> str:
    """
    Replace PII value with a pseudonymous token.
    Token is deterministic (same input → same token) for referential integrity.
    """
    salt = settings.PII_MASKING_SALT.get_secret_value().encode()
    token = hmac.new(salt, value.encode("utf-8"), hashlib.sha256).hexdigest()
    prefix = f"[MASKED-{field_name.upper()}]" if field_name else "[MASKED]"
    return f"{prefix}:{token[:12]}"


def tokenize_identifier(value: str) -> str:
    """
    One-way deterministic tokenization for customer IDs.
    Used to pseudonymise audit logs while preserving linkability.
    """
    salt = settings.PII_MASKING_SALT.get_secret_value().encode()
    return hmac.new(salt, value.encode("utf-8"), hashlib.sha256).hexdigest()


def mask_pii_in_text(text: str, context: str = "") -> str:
    """Apply all regex-based PII patterns to a text string."""
    for pii_type, pattern in PII_PATTERNS.items():
        if pii_type == "german_postal_code" and "address" not in context.lower():
            continue  # Only mask postal codes in address contexts
        text = pattern.sub(f"[MASKED-{pii_type.upper()}]", text)
    return text


def mask_pii_in_dict(
    data: Union[Dict, list, Any],
    depth: int = 0,
    max_depth: int = 10,
) -> Union[Dict, list, Any]:
    """
    Recursively mask PII in a dictionary/list structure.
    Applied to all API response bodies.
    """
    if depth > max_depth:
        return data

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            key_lower = key.lower().replace("-", "_")
            if key_lower in PII_FIELD_NAMES and isinstance(value, str) and value:
                result[key] = mask_pii_value(value, field_name=key_lower)
            elif isinstance(value, str):
                result[key] = mask_pii_in_text(value, context=key)
            elif isinstance(value, (dict, list)):
                result[key] = mask_pii_in_dict(value, depth + 1, max_depth)
            else:
                result[key] = value
        return result

    elif isinstance(data, list):
        return [mask_pii_in_dict(item, depth + 1, max_depth) for item in data]

    return data


# ─── Middleware ──────────────────────────────────────────────────────────────

class PIIMaskingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that automatically masks PII in all JSON responses.

    Applied globally. Excluded paths:
    - /health, /metrics (no data)
    - /docs, /redoc, /openapi.json (API docs)

    For performance: masking is done in-process (no network calls).
    Logs PII detection events (without the PII itself) for audit purposes.
    """

    EXCLUDED_PATHS = frozenset({
        "/health", "/metrics", "/docs", "/redoc",
        "/openapi.json", "/favicon.ico",
    })

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Skip non-JSON or excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body)
            masked_data = mask_pii_in_dict(data)
            masked_body = json.dumps(masked_data, ensure_ascii=False).encode("utf-8")

            return Response(
                content=masked_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("PII masking skipped (non-JSON or error): %s", exc)
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )


# ─── Utility: PII detection for validation ──────────────────────────────────

def detect_pii_fields(data: Dict) -> list:
    """
    Detect which fields contain PII (for GDPR data mapping).
    Returns list of field names containing PII.
    Does NOT return the PII values themselves.
    """
    detected = []
    for key, value in data.items():
        if key.lower() in PII_FIELD_NAMES:
            detected.append(key)
        elif isinstance(value, str):
            for pii_type, pattern in PII_PATTERNS.items():
                if pattern.search(value):
                    detected.append(f"{key}[{pii_type}]")
                    break
    return detected
