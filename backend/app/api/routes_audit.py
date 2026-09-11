from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.audit_service import audit_service
from app.schemas.schemas import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns immutable chronological audit logs of all disaster operations.
    """
    return audit_service.get_logs(db, limit=limit)
