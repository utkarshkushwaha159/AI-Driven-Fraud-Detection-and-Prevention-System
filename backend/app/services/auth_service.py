"""
Authentication service with simple JWT-like token management and role-based access control.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Header, HTTPException, Depends

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


def validate_token(token: str) -> Optional[dict]:
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


def get_current_user_info(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Dependency to extract user info from Authorization header."""
    if not authorization:
        return None
    return validate_token(authorization)


def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency that mandates authentication."""
    user = get_current_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


def require_role(allowed_roles: List[str]):
    """Factory creating dependency enforcing specific user roles."""
    def role_checker(authorization: Optional[str] = Header(None)) -> dict:
        user = get_current_user_info(authorization)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required.")
        user_role = user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access forbidden: requires one of roles {allowed_roles}, but got '{user_role}'."
            )
        return user
    return role_checker
