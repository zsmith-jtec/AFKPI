"""JWT authentication for AFKPI."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.schemas import UserInfo

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer(auto_error=False)

# Simple user store (in production, use database)
# Format: email -> {password_hash, name, role}
USERS = {
    "jesse.schroeder@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Jesse Schroeder", "role": "cfo"},
    "bryan.myers@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Bryan Myers", "role": "controller"},
    "aaron.forinash@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Aaron Forinash", "role": "coo"},
    "andrew.webb@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Andrew Webb", "role": "director"},
    "zach.smith@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Zach Smith", "role": "director"},
    "dan.gannaway@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Dan Gannaway", "role": "director"},
    "mike.chasteen@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Mike Chasteen", "role": "manager"},
    "adam.massens@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Adam Massens", "role": "developer"},
    "peter.hansen@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Peter Hansen", "role": "estimator"},
    "jacob.myers@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Jacob Myers", "role": "sales"},
    "demo@jtec.com": {"password": pwd_context.hash("demo123"), "name": "Demo User", "role": "viewer"},
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


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
