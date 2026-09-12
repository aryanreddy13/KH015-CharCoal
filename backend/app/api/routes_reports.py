from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.report_service import report_service
from app.services.audit_service import audit_service
from app.services.email_service import email_service
from app.schemas.schemas import ReportResponse, ReportCreate, ReportStatusUpdate, ReportActionRequest
from app.websocket.connection_manager import manager
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Citizen Reports"])

def _format_report_dict(report) -> dict:
    return {
        "id": report.id,
        "zone_id": report.zone_id,
        "reporter_id": report.reporter_id,
        "reporter_name": getattr(report, "reporter_name", "Citizen Reporter") or "Citizen Reporter",
        "reporter_phone": getattr(report, "reporter_phone", None),
        "location_text": getattr(report, "location_text", None) or f"{report.latitude:.4f}°, {report.longitude:.4f}°",
        "admin_notes": getattr(report, "admin_notes", None),
        "disaster_type": report.disaster_type,
        "description": report.description,
        "people_affected": report.people_affected,
        "injured_people": report.injured_people,
        "missing_people": report.missing_people,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "photo_url": report.photo_url,
        "status": report.status,
        "priority_score": report.priority_score,
        "priority_level": report.priority_level,
        "assessment": getattr(report, "assessment_json", None) or getattr(report, "assessment", None),
        "priority_assessment": getattr(report, "priority_assessment_json", None) or getattr(report, "priority_assessment", None),
        "created_at": report.created_at.isoformat() + "Z" if report.created_at else None,
        "updated_at": report.updated_at.isoformat() + "Z" if report.updated_at else None,
    }

@router.get("", response_model=List[ReportResponse])
def list_reports(
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Returns submitted citizen emergency reports with optional status filtering.
    """
    return report_service.get_all_reports(db, limit=limit, status_filter=status_filter)

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str, db: Session = Depends(get_db)):
    """
    Returns single incident report detail by ID.
    """
    report = report_service.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report

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

    report_dict = _format_report_dict(report)

    # Dispatch email with attached evidence photo in background
    background_tasks.add_task(
        _dispatch_report_email_background,
        report_dict=report_dict,
        photo_url=report.photo_url or getattr(report_in, "photo_url", None),
    )

    # Broadcast real-time WebSocket events asynchronously
    manager.broadcast_sync("REPORT_RECEIVED", report_dict)

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

@router.patch("/{report_id}/status", response_model=ReportResponse)
def update_report_status_endpoint(
    report_id: str,
    update_in: ReportStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Updates the status of a citizen incident report (e.g. VERIFIED, ACTIONED, RESOLVED, DISMISSED).
    Broadcasts real-time WebSocket event to all connected administrators.
    """
    report = report_service.update_report_status(
        db,
        report_id=report_id,
        new_status=update_in.status,
        notes=update_in.notes,
        actor=update_in.actor or "Command Administrator",
    )
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    log = audit_service.create_log(
        db=db,
        event_type="REPORT_STATUS_CHANGED",
        description=f"Report {report_id[:8]} status updated to {update_in.status} by {update_in.actor}.",
        status="SUCCESS",
        zone_id=report.zone_id,
    )

    report_dict = _format_report_dict(report)
    manager.broadcast_sync("REPORT_UPDATED", report_dict)
    manager.broadcast_sync("AUDIT_LOG_CREATED", {
        "id": log.id,
        "event_type": log.event_type,
        "description": log.description,
        "status": log.status,
        "timestamp": log.timestamp.isoformat() + "Z",
    })

    return report

@router.post("/{report_id}/accept", response_model=ReportResponse)
def accept_report_endpoint(
    report_id: str,
    action_in: Optional[ReportActionRequest] = None,
    db: Session = Depends(get_db),
):
    """
    One-click verification & acceptance of citizen emergency report.
    Instantly changes status to VERIFIED, adds to zone needs, and broadcasts real-time updates.
    """
    notes = action_in.notes if action_in else "Incident verified and accepted by administrator."
    actor = action_in.actor if action_in else "Command Administrator"

    report = report_service.accept_report(db, report_id, notes=notes, actor=actor)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    log = audit_service.create_log(
        db=db,
        event_type="REPORT_ACCEPTED",
        description=f"Citizen Report {report_id[:8]} ({report.disaster_type}) accepted & verified for field response.",
        status="SUCCESS",
        zone_id=report.zone_id,
    )

    report_dict = _format_report_dict(report)
    manager.broadcast_sync("REPORT_UPDATED", report_dict)
    manager.broadcast_sync("ZONE_UPDATED", {"zone_id": report.zone_id, "status": "Critical"})
    manager.broadcast_sync("AUDIT_LOG_CREATED", {
        "id": log.id,
        "event_type": log.event_type,
        "description": log.description,
        "status": log.status,
        "timestamp": log.timestamp.isoformat() + "Z",
    })

    return report

@router.post("/{report_id}/dispatch", response_model=ReportResponse)
def dispatch_report_endpoint(
    report_id: str,
    action_in: Optional[ReportActionRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Dispatches on-scene emergency units to this report location.
    Allocates available emergency resources and broadcasts real-time convoy telemetry.
    """
    notes = action_in.notes if action_in else "Emergency units dispatched to incident location."
    actor = action_in.actor if action_in else "Command Administrator"
    agency_id = action_in.agency_id if action_in else None
    resource_id = action_in.resource_id if action_in else None

    report = report_service.dispatch_report(db, report_id, agency_id=agency_id, resource_id=resource_id, notes=notes, actor=actor)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    log = audit_service.create_log(
        db=db,
        event_type="REPORT_DISPATCHED",
        description=f"Response team dispatched to Citizen Report {report_id[:8]} ({report.disaster_type}).",
        status="SUCCESS",
        zone_id=report.zone_id,
    )

    report_dict = _format_report_dict(report)
    manager.broadcast_sync("REPORT_UPDATED", report_dict)
    manager.broadcast_sync("AUDIT_LOG_CREATED", {
        "id": log.id,
        "event_type": log.event_type,
        "description": log.description,
        "status": log.status,
        "timestamp": log.timestamp.isoformat() + "Z",
    })

    return report

@router.post("/{report_id}/resolve", response_model=ReportResponse)
def resolve_report_endpoint(
    report_id: str,
    action_in: Optional[ReportActionRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Marks a citizen incident report as RESOLVED on the ground.
    """
    notes = action_in.notes if action_in else "Incident resolved on ground."
    actor = action_in.actor if action_in else "Command Administrator"

    report = report_service.resolve_report(db, report_id, notes=notes, actor=actor)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    log = audit_service.create_log(
        db=db,
        event_type="REPORT_RESOLVED",
        description=f"Citizen Report {report_id[:8]} marked as RESOLVED by {actor}.",
        status="SUCCESS",
        zone_id=report.zone_id,
    )

    report_dict = _format_report_dict(report)
    manager.broadcast_sync("REPORT_UPDATED", report_dict)
    manager.broadcast_sync("AUDIT_LOG_CREATED", {
        "id": log.id,
        "event_type": log.event_type,
        "description": log.description,
        "status": log.status,
        "timestamp": log.timestamp.isoformat() + "Z",
    })

    return report

@router.post("/{report_id}/dismiss", response_model=ReportResponse)
def dismiss_report_endpoint(
    report_id: str,
    action_in: Optional[ReportActionRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Dismisses or rejects a duplicate/false report.
    """
    notes = action_in.notes if action_in else "Report dismissed by administrator."
    actor = action_in.actor if action_in else "Command Administrator"

    report = report_service.dismiss_report(db, report_id, notes=notes, actor=actor)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    log = audit_service.create_log(
        db=db,
        event_type="REPORT_DISMISSED",
        description=f"Citizen Report {report_id[:8]} dismissed by {actor}.",
        status="WARNING",
        zone_id=report.zone_id,
    )

    report_dict = _format_report_dict(report)
    manager.broadcast_sync("REPORT_UPDATED", report_dict)
    manager.broadcast_sync("AUDIT_LOG_CREATED", {
        "id": log.id,
        "event_type": log.event_type,
        "description": log.description,
        "status": log.status,
        "timestamp": log.timestamp.isoformat() + "Z",
    })

    return report

@router.delete("/{report_id}")
def delete_report_endpoint(report_id: str, db: Session = Depends(get_db)):
    """
    Deletes a citizen report.
    """
    success = report_service.delete_report(db, report_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    manager.broadcast_sync("REPORT_DELETED", {"id": report_id})
    return {"success": True, "message": f"Report {report_id} deleted successfully"}

