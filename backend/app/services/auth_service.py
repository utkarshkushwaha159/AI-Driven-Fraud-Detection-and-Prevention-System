"""
Authentication service with simple JWT-like token management.
"""
import hashlib
import secrets
import json
import base64
from datetime import datetime, timedelta

# In-memory token store for the prototype
_tokens = {}


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = "fraud_detection_salt_2024"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed


def create_token(user_id: str, username: str, role: str) -> str:
    """Create a simple authentication token."""
    token = secrets.token_urlsafe(32)
    _tokens[token] = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
    }
    return token


def validate_token(token: str) -> dict:
    """Validate a token and return user info, or None."""
    if not token:
        return None
    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    info = _tokens.get(token)
    if not info:
        return None
    # Check expiration
    expires_at = datetime.fromisoformat(info["expires_at"])
    if datetime.utcnow() > expires_at:
        del _tokens[token]
        return None
    return info


def get_current_user(token: str) -> dict:
    """Get user info from token."""
    return validate_token(token)
