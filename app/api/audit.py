"""Audit Log API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import AuditLog
from app.schemas import AuditEntry
from app.auth import get_current_user
from app.schemas import UserInfo

router = APIRouter()


@router.get("", response_model=List[AuditEntry])
def list_audit_entries(
    limit: int = Query(default=100, ge=1, le=1000),
    action: Optional[str] = None,
    user_email: Optional[str] = None,
    entity: Optional[str] = None,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List audit log entries (requires authentication)."""
    query = db.query(AuditLog).order_by(desc(AuditLog.timestamp))

    if action:
        query = query.filter(AuditLog.action == action)
    if user_email:
        query = query.filter(AuditLog.user_email == user_email)
    if entity:
        query = query.filter(AuditLog.entity == entity)

    entries = query.limit(limit).all()
    return entries
