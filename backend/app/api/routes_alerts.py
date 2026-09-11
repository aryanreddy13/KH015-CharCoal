from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.alert_service import alert_service
from app.services.audit_service import audit_service
from app.schemas.schemas import AlertResponse, AlertCreate
from app.websocket.connection_manager import manager

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertResponse])
def list_alerts(db: Session = Depends(get_db)):
    """
    Returns active alerts ordered by priority and recency.
    """
    return alert_service.get_active_alerts(db)

@router.post("", response_model=AlertResponse)
async def create_alert(alert_in: AlertCreate, db: Session = Depends(get_db)):
    """
    Creates a new operational emergency alert and broadcasts to WebSocket subscribers.
    """
    alert = alert_service.create_alert(db, alert_in)
    
    # Broadcast alert
    await manager.broadcast("ALERT_CREATED", {
        "id": alert.id,
        "zone_id": alert.zone_id,
        "title": alert.title,
        "message": alert.message,
        "alert_level": alert.alert_level,
    })

    # Log audit event
    audit_service.create_log(
        db=db,
        event_type="ALERT_CREATED",
        description=f"Alert raised: {alert.title}",
        status="WARNING" if alert.alert_level == "WARNING" else "FAILURE" if alert.alert_level == "CRITICAL" else "SUCCESS",
        zone_id=alert.zone_id,
    )

    return alert
