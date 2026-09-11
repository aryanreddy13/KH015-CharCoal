import json
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import SOSEvent, Agency, Resource, AuditLog, Zone
from app.schemas.schemas import (
    ProviderIncidentResponse,
    ProviderKPIsResponse,
    ProviderActionRequest,
    ProviderActionResponse,
    AgencyResponse,
)
from app.services.audit_service import audit_service
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/provider", tags=["Emergency Service Providers"])

VALID_TRANSITIONS = {
    "NEW": ["ACCEPTED", "DISPATCHED"],
    "ACCEPTED": ["DISPATCHED", "EN_ROUTE"],
    "DISPATCHED": ["EN_ROUTE", "ARRIVED"],
    "EN_ROUTE": ["ARRIVED", "RESOLVED"],
    "ARRIVED": ["RESOLVED"],
    "RESOLVED": [],
}

def format_incident_response(ev: SOSEvent) -> ProviderIncidentResponse:
    req_res = json.loads(ev.required_resources_json) if ev.required_resources_json else ["Rescue", "Medical"]
    zone_name = ev.zone.name if ev.zone else "Emergency Zone Alpha"
    agency_name = ev.assigned_agency.name if ev.assigned_agency else "Emergency Service Dispatch"
    resource_name = ev.assigned_resource.name if ev.assigned_resource else "Rapid Water Rescue Team 01"

    return ProviderIncidentResponse(
        id=ev.id,
        incident_id=ev.incident_id or f"SOS-{ev.id[:4].upper()}",
        disaster_type=ev.disaster_type or "Flood",
        zone_name=zone_name,
        zone_id=ev.zone_id,
        severity=ev.severity or 9.5,
        priority_score=ev.priority_score,
        priority_level=ev.priority_level,
        priority_assessment=ev.priority_assessment_json,
        location_text=f"{ev.latitude:.4f}, {ev.longitude:.4f}",
        latitude=ev.latitude,
        longitude=ev.longitude,
        accuracy=ev.accuracy or 10.0,
        people_affected=ev.people_affected or 1,
        injured_people=ev.injured_people or 0,
        missing_people=ev.missing_people or 0,
        required_resources=req_res,
        distance_km=ev.distance_km or 4.8,
        eta_minutes=ev.eta_minutes or 11,
        photo_url=ev.photo_url,
        provider_status=ev.provider_status or "NEW",
        assigned_agency_id=ev.assigned_agency_id,
        assigned_agency_name=agency_name,
        assigned_resource_id=ev.assigned_resource_id,
        assigned_resource_name=resource_name,
        resend_status=ev.resend_status or "SENT",
        pagerduty_status=ev.pagerduty_status or "SENT",
        created_at=ev.created_at.isoformat() + "Z" if ev.created_at else datetime.utcnow().isoformat() + "Z",
    )

@router.get("/agencies", response_model=List[AgencyResponse])
def get_provider_agencies(db: Session = Depends(get_db)):
    """
    Returns all 5 emergency response provider agencies.
    """
    return db.query(Agency).filter(Agency.status == "ACTIVE").all()

@router.get("/kpis", response_model=ProviderKPIsResponse)
def get_provider_kpis(
    agency_type: Optional[str] = Query(None, description="Agency type e.g. FIRE_RESCUE, MEDICAL, POLICE, NGO, GOVERNMENT"),
    agency_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Returns live operational KPIs for the selected emergency service provider.
    """
    agency = None
    if agency_id:
        agency = db.query(Agency).filter(Agency.id == agency_id).first()
    elif agency_type:
        agency = db.query(Agency).filter(Agency.type == agency_type.upper()).first()

    agency_name = agency.name if agency else "Central Operations"
    curr_type = agency.type if agency else (agency_type or "ALL")

    # Query incidents
    all_sos = db.query(SOSEvent).all()
    
    # Filter for agency relevance
    relevant = []
    for s in all_sos:
        notified = json.loads(s.notified_agencies_json) if s.notified_agencies_json else []
        notified_types = [n.get("agency_type") for n in notified]
        if not curr_type or curr_type == "ALL" or curr_type in notified_types or s.assigned_agency_id == (agency.id if agency else None):
            relevant.append(s)

    active_incidents = len([s for s in relevant if s.provider_status != "RESOLVED"])
    critical_incidents = len([s for s in relevant if (s.severity or 0) >= 8.0 and s.provider_status != "RESOLVED"])
    people_affected = sum((s.people_affected or 0) for s in relevant if s.provider_status != "RESOLVED")

    # Resource counts
    res_query = db.query(Resource)
    if agency:
        res_query = res_query.filter(Resource.agency_id == agency.id)
    all_res = res_query.all()

    available_units = len([r for r in all_res if r.status == "AVAILABLE"])
    units_deployed = len([r for r in all_res if r.status in ("ALLOCATED", "EN_ROUTE")])

    return ProviderKPIsResponse(
        agency_id=agency.id if agency else None,
        agency_name=agency_name,
        agency_type=curr_type,
        active_incidents=active_incidents,
        critical_incidents=critical_incidents,
        available_units=available_units,
        units_deployed=units_deployed,
        people_affected=people_affected,
    )

@router.get("/incidents", response_model=List[ProviderIncidentResponse])
def list_provider_incidents(
    agency_type: Optional[str] = Query(None),
    agency_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Returns incident cards tailored to the logged-in emergency service provider.
    Surfaces both directly assigned and coordination-routed incidents.
    """
    query = db.query(SOSEvent).order_by(SOSEvent.created_at.desc())
    if status_filter:
        query = query.filter(SOSEvent.provider_status == status_filter.upper())

    all_sos = query.all()
    results = []

    for s in all_sos:
        notified = json.loads(s.notified_agencies_json) if s.notified_agencies_json else []
        notified_types = [n.get("agency_type") for n in notified]
        notified_ids = [n.get("agency_id") for n in notified]

        # Match agency if requested
        if agency_type and agency_type.upper() != "ALL":
            if agency_type.upper() not in notified_types and s.assigned_agency_id != agency_id:
                # Also check if severity >= 9.0 (all providers receive critical awareness)
                if (s.severity or 0) < 9.0:
                    continue

        if agency_id:
            if agency_id not in notified_ids and s.assigned_agency_id != agency_id:
                if (s.severity or 0) < 9.0:
                    continue

        results.append(format_incident_response(s))

    level_ranks = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    results.sort(
        key=lambda item: (
            level_ranks.get((item.priority_level or "LOW").upper(), 0),
            float(item.priority_score or item.severity or 0.0),
            item.created_at or "",
        ),
        reverse=True,
    )

    return results

@router.get("/incidents/{incident_id}", response_model=ProviderIncidentResponse)
def get_incident_detail(incident_id: str, db: Session = Depends(get_db)):
    """
    Returns full incident details for provider tactical modal.
    """
    ev = db.query(SOSEvent).filter((SOSEvent.id == incident_id) | (SOSEvent.incident_id == incident_id)).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency incident not found.")
    return format_incident_response(ev)

async def handle_state_transition(
    incident_id: str,
    target_status: str,
    req: Optional[ProviderActionRequest],
    db: Session,
) -> ProviderActionResponse:
    ev = db.query(SOSEvent).filter((SOSEvent.id == incident_id) | (SOSEvent.incident_id == incident_id)).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency incident not found.")

    current = ev.provider_status or "NEW"
    valid_next = VALID_TRANSITIONS.get(current, [])

    if target_status not in valid_next and target_status != current:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from '{current}' to '{target_status}'. Valid next states: {valid_next}",
        )

    ev.provider_status = target_status
    if req and req.agency_id:
        ev.assigned_agency_id = req.agency_id
    if req and req.resource_id:
        ev.assigned_resource_id = req.resource_id
        # Update resource status
        res = db.query(Resource).filter(Resource.id == req.resource_id).first()
        if res:
            if target_status == "DISPATCHED":
                res.status = "ALLOCATED"
            elif target_status in ("EN_ROUTE", "ARRIVED"):
                res.status = "EN_ROUTE"
            elif target_status == "RESOLVED":
                res.status = "AVAILABLE"

    if target_status == "RESOLVED":
        ev.status = "RESOLVED"

    db.commit()
    db.refresh(ev)

    # Create Audit Log
    agency_name = ev.assigned_agency.name if ev.assigned_agency else "Emergency Provider"
    log = audit_service.create_log(
        db=db,
        event_type=f"INCIDENT_{target_status}",
        description=f"Incident [{ev.incident_id}] state transitioned to {target_status} by {agency_name}. {req.notes if req and req.notes else ''}",
        status="SUCCESS",
        zone_id=ev.zone_id,
        agency_id=ev.assigned_agency_id,
        metadata_dict={"incident_id": ev.incident_id, "prev_status": current, "new_status": target_status},
    )

    formatted = format_incident_response(ev)

    # Broadcast WebSocket events
    event_name = f"INCIDENT_{target_status}"
    if target_status == "DISPATCHED":
        event_name = "RESOURCE_DISPATCHED"
    elif target_status == "EN_ROUTE":
        event_name = "ETA_UPDATED"

    try:
        await manager.broadcast(event_name, formatted.model_dump())
        await manager.broadcast("AUDIT_LOG_CREATED", {
            "id": log.id,
            "event_type": log.event_type,
            "description": log.description,
            "status": log.status,
            "timestamp": log.timestamp.isoformat() + "Z",
        })
    except Exception as ws_err:
        logger.warning(f"WebSocket broadcast error during transition: {ws_err}")

    return ProviderActionResponse(
        success=True,
        message=f"Incident {ev.incident_id} successfully updated to {target_status}.",
        incident_id=ev.incident_id,
        new_status=target_status,
        incident=formatted,
    )

@router.post("/incidents/{incident_id}/accept", response_model=ProviderActionResponse)
async def accept_incident(
    incident_id: str,
    req: Optional[ProviderActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Provider acknowledges and accepts emergency response responsibility."""
    return await handle_state_transition(incident_id, "ACCEPTED", req, db)

@router.post("/incidents/{incident_id}/dispatch", response_model=ProviderActionResponse)
async def dispatch_incident_unit(
    incident_id: str,
    req: Optional[ProviderActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Provider assigns specific tactical unit and authorizes mobilization."""
    return await handle_state_transition(incident_id, "DISPATCHED", req, db)

@router.post("/incidents/{incident_id}/en-route", response_model=ProviderActionResponse)
async def mark_incident_en_route(
    incident_id: str,
    req: Optional[ProviderActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Provider confirms unit is wheels-up / en route to GPS destination."""
    return await handle_state_transition(incident_id, "EN_ROUTE", req, db)

@router.post("/incidents/{incident_id}/arrived", response_model=ProviderActionResponse)
async def mark_incident_arrived(
    incident_id: str,
    req: Optional[ProviderActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Provider confirms on-scene arrival and beginning of extraction/treatment."""
    return await handle_state_transition(incident_id, "ARRIVED", req, db)

@router.post("/incidents/{incident_id}/resolve", response_model=ProviderActionResponse)
async def resolve_incident(
    incident_id: str,
    req: Optional[ProviderActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Provider concludes rescue operations and marks incident safely resolved."""
    return await handle_state_transition(incident_id, "RESOLVED", req, db)
