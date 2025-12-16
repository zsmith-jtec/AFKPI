"""JWT authentication for AFKPI.

NOTE: This is a demo/prototype implementation.
For production, use a proper user database with hashed passwords.
"""
from datetime import datetime, timedelta
from typing import Optional
from hashlib import sha256
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.schemas import UserInfo

# Bearer token security
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Simple password hashing for demo. Use bcrypt in production."""
    return sha256(password.encode()).hexdigest()


# Demo password hash (sha256 of "demo123")
DEMO_HASH = hash_password("demo123")

# Simple user store (in production, use database)
# Format: email -> {password_hash, name, role}
USERS = {
    "jschroeder@jtecindustries.com": {"password": DEMO_HASH, "name": "Jesse Schroeder", "role": "cfo"},
    "bmyers@jtecindustries.com": {"password": DEMO_HASH, "name": "Bryan Myers", "role": "controller"},
    "aforinash@jtecindustries.com": {"password": DEMO_HASH, "name": "Aaron Forinash", "role": "coo"},
    "awebb@jtecindustries.com": {"password": DEMO_HASH, "name": "Andrew Webb", "role": "director"},
    "zsmith@jtecindustries.com": {"password": DEMO_HASH, "name": "Zach Smith", "role": "director"},
    "dgannaway@jtecindustries.com": {"password": DEMO_HASH, "name": "Dan Gannaway", "role": "director"},
    "mchasteen@jtecindustries.com": {"password": DEMO_HASH, "name": "Mike Chasteen", "role": "manager"},
    "amassens@jtecindustries.com": {"password": DEMO_HASH, "name": "Adam Massens", "role": "developer"},
    "phansen@jtecindustries.com": {"password": DEMO_HASH, "name": "Peter Hansen", "role": "estimator"},
    "jmyers@jtecindustries.com": {"password": DEMO_HASH, "name": "Jacob Myers", "role": "sales"},
    "demo@jtecindustries.com": {"password": DEMO_HASH, "name": "Demo User", "role": "viewer"},
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain_password) == hashed_password


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate user by email and password."""
    user = USERS.get(email.lower())
    if not user:
        return None
    if not verify_password(password, user["password"]):
        return None
    return {"email": email.lower(), "name": user["name"], "role": user["role"]}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserInfo:
    """Get current user from JWT token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user_data = USERS.get(email)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return UserInfo(email=email, name=user_data["name"], role=user_data["role"])


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserInfo]:
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
