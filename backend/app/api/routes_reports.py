from typing import List
import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.report_service import report_service
from app.services.audit_service import audit_service
from app.services.email_service import email_service
from app.schemas.schemas import ReportResponse, ReportCreate
from app.websocket.connection_manager import manager
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Citizen Reports"])

@router.get("", response_model=List[ReportResponse])
def list_reports(limit: int = 100, db: Session = Depends(get_db)):
    """
    Returns submitted citizen emergency reports.
    """
    return report_service.get_all_reports(db, limit=limit)

def _dispatch_report_email_background(report_dict: dict, photo_url: str = None):
    try:
        primary_recipient = getattr(settings, "NOTIFICATION_EMAIL", "aryanreddy2006@gmail.com")
        if primary_recipient:
            email_service.send_report_email(
                recipient=primary_recipient,
                report_data=report_dict,
                photo_url=photo_url,
            )
    except Exception as e:
        logger.error(f"Failed to dispatch citizen report email: {e}")

@router.post("", response_model=ReportResponse)
def create_citizen_report(
    report_in: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Submits a new citizen emergency report from the mobile reporter interface.
    Broadcasts real-time WebSockets and dispatches emergency email with evidence photo to disaster authorities.
    """
    report = report_service.create_report(db, report_in)

    # Log to audit trail
    log = audit_service.create_log(
        db=db,
        event_type="REPORT_RECEIVED",
        description=f"Citizen Emergency Report received: {report.disaster_type} affecting ~{report.people_affected} people.",
        status="SUCCESS",
        zone_id=report.zone_id,
        metadata_dict={
            "report_id": report.id,
            "injured": report.injured_people,
            "missing": report.missing_people,
            "coords": [report.latitude, report.longitude],
            "has_photo": bool(report.photo_url),
        },
    )

    report_dict = {
        "id": report.id,
        "disaster_type": report.disaster_type,
        "description": report.description,
        "people_affected": report.people_affected,
        "injured_people": report.injured_people,
        "missing_people": report.missing_people,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "location_text": getattr(report, "location_text", None) or f"{report.latitude:.4f}, {report.longitude:.4f}",
        "reporter_name": getattr(report, "reporter_name", "Citizen"),
        "reporter_phone": getattr(report, "reporter_phone", None),
        "status": report.status,
        "created_at": report.created_at.isoformat() + "Z",
    }

    # Dispatch email with attached evidence photo in background
    background_tasks.add_task(
        _dispatch_report_email_background,
        report_dict=report_dict,
        photo_url=report.photo_url or getattr(report_in, "photo_url", None),
    )

    # Broadcast real-time WebSocket events asynchronously
    manager.broadcast_sync("REPORT_RECEIVED", {
        "id": report.id,
        "zone_id": report.zone_id,
        "disaster_type": report.disaster_type,
        "description": report.description,
        "people_affected": report.people_affected,
        "injured_people": report.injured_people,
        "missing_people": report.missing_people,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "status": report.status,
        "created_at": report.created_at.isoformat() + "Z",
    })

    if report.assessment_json:
        manager.broadcast_sync("ASSESSMENT_COMPLETED", {
            "event": "ASSESSMENT_COMPLETED",
            "version": report.assessment_version or "1.0",
            "report_id": report.id,
            "incident_id": report.id,
            "assessment": report.assessment_json,
        })

    if getattr(report, "priority_assessment_json", None):
        manager.broadcast_sync("PRIORITY_ASSESSMENT_COMPLETED", {
            "event": "PRIORITY_ASSESSMENT_COMPLETED",
            "report_id": report.id,
            "incident_id": report.id,
            "zone_score": report.priority_score,
            "priority_level": report.priority_level,
            "priority_assessment": report.priority_assessment_json,
        })

    manager.broadcast_sync("AUDIT_LOG_CREATED", {
        "id": log.id,
        "event_type": log.event_type,
        "description": log.description,
        "status": log.status,
        "timestamp": log.timestamp.isoformat() + "Z",
    })

    return report
