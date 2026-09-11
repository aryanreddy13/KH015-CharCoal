import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import AuditLog

class AuditService:
    @staticmethod
    def create_log(
        db: Session,
        event_type: str,
        description: str,
        status: str = "SUCCESS",
        zone_id: Optional[str] = None,
        agency_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata_dict: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        meta_str = json.dumps(metadata_dict) if metadata_dict else None
        log = AuditLog(
            event_type=event_type,
            description=description,
            status=status,
            zone_id=zone_id,
            agency_id=agency_id,
            user_id=user_id,
            metadata_json=meta_str,
            timestamp=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_logs(db: Session, limit: int = 50) -> List[AuditLog]:
        return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

audit_service = AuditService()
