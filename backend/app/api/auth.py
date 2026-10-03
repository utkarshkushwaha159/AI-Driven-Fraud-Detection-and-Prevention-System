"""
Authentication API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.schemas import LoginRequest, LoginResponse, UserOut
from app.services.auth_service import hash_password, verify_password, create_token, validate_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return token."""
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.id, user.username, user.role.value if hasattr(user.role, 'value') else user.role)
    return LoginResponse(
        token=token,
        user_id=user.id,
        username=user.username,
        role=user.role.value if hasattr(user.role, 'value') else user.role,
        full_name=user.full_name,
    )


@router.get("/me")
def get_me(token: str = None, db: Session = Depends(get_db)):
    """Get current user info from token."""
    from fastapi import Header
    # Token from query param for simplicity
    user_info = validate_token(token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_info


@router.get("/users", response_model=list)
def list_users(db: Session = Depends(get_db)):
    """List all users (admin only in production)."""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value if hasattr(u.role, 'value') else u.role,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]
