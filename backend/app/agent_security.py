from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

import jwt
from jwt import InvalidTokenError

from app.config import settings


def _agent_jwt_secret() -> str:
    return settings.AGENT_JWT_SECRET or settings.JWT_SECRET


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def verify_secret(secret: str, expected_hash: str) -> bool:
    provided_hash = hash_secret(secret)
    return hmac.compare_digest(provided_hash, expected_hash)


def generate_key_id() -> str:
    return f"ak_{secrets.token_urlsafe(18)}"


def generate_secret() -> str:
    return f"as_{secrets.token_urlsafe(32)}"


def create_agent_access_token(agent_id: str, scopes: list[str]) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.AGENT_JWT_EXPIRE_MINUTES)
    payload = {
        "sub": agent_id,
        "actor_type": "agent",
        "scopes": scopes,
        "aud": settings.AGENT_JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, _agent_jwt_secret(), algorithm="HS256")


def decode_agent_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        _agent_jwt_secret(),
        algorithms=["HS256"],
        audience=settings.AGENT_JWT_AUDIENCE,
    )


__all__ = [
    "InvalidTokenError",
    "create_agent_access_token",
    "decode_agent_access_token",
    "generate_key_id",
    "generate_secret",
    "hash_secret",
    "verify_secret",
]

