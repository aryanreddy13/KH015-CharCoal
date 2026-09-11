from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Alert
from app.schemas.schemas import AlertCreate

class AlertService:
    @staticmethod
    def get_active_alerts(db: Session, limit: int = 50) -> List[Alert]:
        return db.query(Alert).filter(Alert.is_active == True).order_by(Alert.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_all_alerts(db: Session, limit: int = 100) -> List[Alert]:
        return db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()

    @staticmethod
    def create_alert(db: Session, alert_in: AlertCreate) -> Alert:
        alert = Alert(
            zone_id=alert_in.zone_id,
            title=alert_in.title,
            message=alert_in.message,
            alert_level=alert_in.alert_level,
            is_active=alert_in.is_active,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

alert_service = AlertService()
