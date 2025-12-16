"""Authentication API endpoints."""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import TokenRequest, TokenResponse, UserInfo
from app.auth import authenticate_user, create_access_token, get_current_user
from app.models import AuditLog

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(request: TokenRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user["email"], "name": user["name"], "role": user["role"]},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    # Log the login
    audit_entry = AuditLog(
        user_email=user["email"],
        action="LOGIN",
        entity="auth",
        details=f"User {user['name']} logged in"
    )
    db.add(audit_entry)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.get("/me", response_model=UserInfo)
def get_me(current_user: UserInfo = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user
