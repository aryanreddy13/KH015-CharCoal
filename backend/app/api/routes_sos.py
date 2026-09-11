import json
from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.sos_service import sos_service
from app.schemas.schemas import SOSCreate, SOSResponse
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sos", tags=["Citizen SOS Beacon"])

@router.get("", response_model=List[SOSResponse])
def list_sos_events(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns active and recent SOS emergency beacons for authority monitors.
    """
    events = sos_service.get_all_sos(db, limit=limit)
    res = []
    for ev in events:
        req_res = json.loads(ev.required_resources_json) if ev.required_resources_json else ["Rescue", "Medical"]
        notified = json.loads(ev.notified_agencies_json) if ev.notified_agencies_json else []
        
        allocations_list = []
        if hasattr(ev, "resource_allocations") and ev.resource_allocations:
            for al in ev.resource_allocations:
                allocations_list.append({
                    "id": al.id,
                    "resource_id": al.resource_id,
                    "resource_name": al.resource.name if al.resource else al.resource_type,
                    "agency_name": al.provider_agency.name if al.provider_agency else None,
                    "resource_type": al.resource_type,
                    "requested_quantity": al.requested_quantity,
                    "recommended_quantity": al.recommended_quantity,
                    "allocated_quantity": al.allocated_quantity,
                    "status": al.status,
                    "notes": al.notes,
                    "unit": al.resource.unit if al.resource else "Units",
                })

        res.append(
            SOSResponse(
                id=ev.id,
                incident_id=ev.incident_id or f"SOS-{ev.id[:4].upper()}",
                status=ev.status or "ACTIVATED",
                provider_status=ev.provider_status or "NEW",
                message="Active emergency beacon",
                latitude=ev.latitude,
                longitude=ev.longitude,
                accuracy=ev.accuracy,
                reporter_name=ev.reporter_name,
                disaster_type=ev.disaster_type or "Flood",
                severity=ev.severity or 9.5,
                people_affected=ev.people_affected or 1,
                injured_people=ev.injured_people or 0,
                missing_people=ev.missing_people or 0,
                food_required=ev.food_required or False,
                food_quantity=ev.food_quantity,
                water_required=ev.water_required or False,
                water_quantity=ev.water_quantity,
                shelter_required=ev.shelter_required or False,
                shelter_quantity=ev.shelter_quantity,
                medicine_required=ev.medicine_required or False,
                medicine_quantity=ev.medicine_quantity,
                rescue_required=ev.rescue_required or False,
                rescue_units_required=ev.rescue_units_required,
                ambulance_required=ev.ambulance_required or False,
                ambulances_required=ev.ambulances_required,
                photo_url=ev.photo_url,
                distance_km=ev.distance_km or 4.8,
                eta_minutes=ev.eta_minutes or 11,
                required_resources=req_res,
                notified_agencies=notified,
                resource_allocations=allocations_list,
                assessment=ev.assessment_json,
                priority_assessment=ev.priority_assessment_json,
                priority_level=ev.priority_level,
                priority_score=ev.priority_score,
                resend_status=ev.resend_status or "NOT_SENT",
                pagerduty_status=ev.pagerduty_status or "NOT_SENT",
                created_at=ev.created_at,
            )
        )
    return res

@router.post("", response_model=SOSResponse, status_code=status.HTTP_201_CREATED)
def trigger_emergency_sos(
    sos_in: SOSCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Triggers an instant high-priority emergency SOS signal from citizen mobile app.
    Persists to Supabase, determines agency routing, calculates ETA, triggers alerts,
    broadcasts real-time WebSockets, and dispatches background notifications (Resend + PagerDuty).
    """
    # Validation: Coordinates range
    if not (-90.0 <= sos_in.latitude <= 90.0) or not (-180.0 <= sos_in.longitude <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid GPS coordinates supplied. Latitude must be in [-90, 90], Longitude in [-180, 180].",
        )

    try:
        sos_event, alert, log = sos_service.create_sos(db, sos_in)
    except Exception as e:
        logger.error(f"Failed to process SOS event: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register SOS emergency signal.",
        )

    # Parse JSON fields and allocations
    req_res = json.loads(sos_event.required_resources_json) if sos_event.required_resources_json else ["Rescue", "Medical"]
    notified_agencies = json.loads(sos_event.notified_agencies_json) if sos_event.notified_agencies_json else []
    zone_title = sos_event.zone.name if sos_event.zone else "Zone Alpha"

    allocations_list = []
    if hasattr(sos_event, "resource_allocations") and sos_event.resource_allocations:
        for al in sos_event.resource_allocations:
            allocations_list.append({
                "id": al.id,
                "resource_id": al.resource_id,
                "resource_name": al.resource.name if al.resource else al.resource_type,
                "agency_name": al.provider_agency.name if al.provider_agency else None,
                "resource_type": al.resource_type,
                "requested_quantity": al.requested_quantity,
                "recommended_quantity": al.recommended_quantity,
                "allocated_quantity": al.allocated_quantity,
                "status": al.status,
                "notes": al.notes,
                "unit": al.resource.unit if al.resource else "Units",
            })

    incident_dict = {
        "id": sos_event.id,
        "incident_id": sos_event.incident_id,
        "disaster_type": sos_event.disaster_type or "Flood",
        "zone_name": zone_title,
        "zone_id": sos_event.zone_id,
        "severity": sos_event.severity or 9.5,
        "priority_score": sos_event.priority_score,
        "priority_level": sos_event.priority_level,
        "location_text": f"{sos_event.latitude:.4f}, {sos_event.longitude:.4f}",
        "latitude": sos_event.latitude,
        "longitude": sos_event.longitude,
        "accuracy": sos_event.accuracy or 10.0,
        "people_affected": sos_event.people_affected or 1,
        "injured_people": sos_event.injured_people or 0,
        "missing_people": sos_event.missing_people or 0,
        "required_resources": req_res,
        "resource_allocations": allocations_list,
        "distance_km": sos_event.distance_km or 4.8,
        "eta_minutes": sos_event.eta_minutes or 11,
        "photo_url": sos_event.photo_url,
        "provider_status": sos_event.provider_status or "NEW",
        "assigned_agency_id": sos_event.assigned_agency_id,
        "assigned_agency_name": sos_event.assigned_agency.name if sos_event.assigned_agency else "Emergency Services",
        "assigned_resource_id": sos_event.assigned_resource_id,
        "assigned_resource_name": sos_event.assigned_resource.name if sos_event.assigned_resource else "Rapid Unit 01",
        "resend_status": "QUEUED",
        "pagerduty_status": "QUEUED",
        "created_at": sos_event.created_at.isoformat() + "Z",
    }

    # Asynchronous non-blocking dispatch of Resend & PagerDuty in background
    background_tasks.add_task(
        sos_service.dispatch_notifications_background,
        sos_id=sos_event.id,
        incident_data=incident_dict,
        routed_agencies=notified_agencies,
        photo_url=sos_event.photo_url,
    )

    # Broadcast real-time WebSocket events asynchronously
    try:
        # 1. SOS_ACTIVATED
        manager.broadcast_sync("SOS_ACTIVATED", incident_dict)

        # 2. PROVIDER_INCIDENT_CREATED
        manager.broadcast_sync("PROVIDER_INCIDENT_CREATED", incident_dict)

        # 3. ALERT_CREATED
        manager.broadcast_sync("ALERT_CREATED", {
            "id": alert.id,
            "zone_id": alert.zone_id,
            "title": alert.title,
            "message": alert.message,
            "alert_level": alert.alert_level,
            "created_at": alert.created_at.isoformat() + "Z",
        })

        # 4. ASSESSMENT_COMPLETED
        if sos_event.assessment_json:
            manager.broadcast_sync("ASSESSMENT_COMPLETED", {
                "event": "ASSESSMENT_COMPLETED",
                "version": sos_event.assessment_version or "1.0",
                "incident_id": sos_event.incident_id,
                "sos_id": sos_event.id,
                "assessment": sos_event.assessment_json,
            })

        # 5. PRIORITY_ASSESSMENT_COMPLETED
        if getattr(sos_event, "priority_assessment_json", None):
            manager.broadcast_sync("PRIORITY_ASSESSMENT_COMPLETED", {
                "event": "PRIORITY_ASSESSMENT_COMPLETED",
                "incident_id": sos_event.incident_id,
                "zone_score": sos_event.priority_score,
                "priority_level": sos_event.priority_level,
                "priority_assessment": sos_event.priority_assessment_json,
            })

        # 6. AUDIT_LOG_CREATED
        manager.broadcast_sync("AUDIT_LOG_CREATED", {
            "id": log.id,
            "event_type": log.event_type,
            "description": log.description,
            "status": log.status,
            "timestamp": log.timestamp.isoformat() + "Z",
        })
    except Exception as ws_err:
        logger.warning(f"WebSocket broadcast during SOS encounter warning: {ws_err}")

    return SOSResponse(
        id=sos_event.id,
        incident_id=sos_event.incident_id,
        status="ACTIVATED",
        provider_status=sos_event.provider_status or "NEW",
        message="Emergency signal received and providers dispatched",
        latitude=sos_event.latitude,
        longitude=sos_event.longitude,
        accuracy=sos_event.accuracy,
        reporter_name=sos_event.reporter_name,
        disaster_type=sos_event.disaster_type or "Flood",
        severity=sos_event.severity or 9.5,
        people_affected=sos_event.people_affected or 1,
        injured_people=sos_event.injured_people or 0,
        missing_people=sos_event.missing_people or 0,
        food_required=sos_event.food_required or False,
        food_quantity=sos_event.food_quantity,
        water_required=sos_event.water_required or False,
        water_quantity=sos_event.water_quantity,
        shelter_required=sos_event.shelter_required or False,
        shelter_quantity=sos_event.shelter_quantity,
        medicine_required=sos_event.medicine_required or False,
        medicine_quantity=sos_event.medicine_quantity,
        rescue_required=sos_event.rescue_required or False,
        rescue_units_required=sos_event.rescue_units_required,
        ambulance_required=sos_event.ambulance_required or False,
        ambulances_required=sos_event.ambulances_required,
        photo_url=sos_event.photo_url,
        distance_km=sos_event.distance_km or 4.8,
        eta_minutes=sos_event.eta_minutes or 11,
        required_resources=req_res,
        notified_agencies=notified_agencies,
        resource_allocations=allocations_list,
        assessment=sos_event.assessment_json,
        priority_assessment=sos_event.priority_assessment_json,
        priority_level=sos_event.priority_level,
        priority_score=sos_event.priority_score,
        resend_status="QUEUED",
        pagerduty_status="QUEUED",
        created_at=sos_event.created_at,
    )
