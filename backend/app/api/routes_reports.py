from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.report_service import report_service
from app.services.audit_service import audit_service
from app.schemas.schemas import ReportResponse, ReportCreate
from app.websocket.connection_manager import manager

router = APIRouter(prefix="/reports", tags=["Citizen Reports"])

@router.get("", response_model=List[ReportResponse])
def list_reports(limit: int = 100, db: Session = Depends(get_db)):
    """
    Returns submitted citizen emergency reports.
    """
    return report_service.get_all_reports(db, limit=limit)

@router.post("", response_model=ReportResponse)
def create_citizen_report(report_in: ReportCreate, db: Session = Depends(get_db)):
    """
    Submits a new citizen emergency report from the mobile reporter interface.
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
        },
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
