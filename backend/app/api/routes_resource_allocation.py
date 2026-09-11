import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import ResourceAllocation, Resource, Agency
from app.schemas.schemas import (
    ResourceAllocationResponse,
    ResourceInventoryResponse,
    ResourceSummaryStats,
)
from app.services.resource_allocation_service import resource_allocation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resource-allocations", tags=["Resource Allotment & Dispatch"])

@router.get("", response_model=List[ResourceAllocationResponse])
def list_resource_allocations(
    incident_id: Optional[str] = Query(None, description="Filter by incident ID"),
    agency_type: Optional[str] = Query(None, description="Filter by agency type (NGO, FIRE_RESCUE, MEDICAL, etc.)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by allocation status"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Lists resource allocations across incidents with filtering by incident, agency, or status.
    """
    query = db.query(ResourceAllocation).join(Resource, ResourceAllocation.resource_id == Resource.id).join(Agency, ResourceAllocation.provider_agency_id == Agency.id)
    
    if incident_id:
        query = query.filter(ResourceAllocation.incident_id == incident_id)
    if agency_type:
        query = query.filter(Agency.type == agency_type)
    if status_filter:
        query = query.filter(ResourceAllocation.status == status_filter)

    records = query.order_by(ResourceAllocation.created_at.desc()).limit(limit).all()

    result = []
    for r in records:
        result.append(
            ResourceAllocationResponse(
                id=r.id,
                incident_id=r.incident_id,
                sos_id=r.sos_id,
                resource_id=r.resource_id,
                provider_agency_id=r.provider_agency_id,
                resource_type=r.resource_type,
                requested_quantity=r.requested_quantity,
                recommended_quantity=r.recommended_quantity,
                allocated_quantity=r.allocated_quantity,
                status=r.status,
                allocated_by=r.allocated_by,
                allocated_at=r.allocated_at,
                dispatched_at=r.dispatched_at,
                delivered_at=r.delivered_at,
                cancelled_at=r.cancelled_at,
                notes=r.notes,
                created_at=r.created_at,
                updated_at=r.updated_at,
                resource_name=r.resource.name if r.resource else r.resource_type,
                agency_name=r.provider_agency.name if r.provider_agency else None,
                unit=r.resource.unit if r.resource else "Units",
            )
        )
    return result

@router.get("/inventory")
def get_resource_inventory(
    agency_type: Optional[str] = Query(None, description="Filter by agency type: NGO, FIRE_RESCUE, MEDICAL, POLICE"),
    db: Session = Depends(get_db),
):
    """
    Retrieves real-time agency inventory levels, showing total, available, allocated, and reserved units.
    """
    return resource_allocation_service.get_agency_inventory(db, agency_type=agency_type)

@router.get("/summary", response_model=ResourceSummaryStats)
def get_resource_summary(db: Session = Depends(get_db)):
    """
    Retrieves high-level resource allotment metrics, fulfillment percentages, and shortage logs.
    """
    return resource_allocation_service.get_summary_stats(db)

@router.post("/{allocation_id}/approve", response_model=ResourceAllocationResponse)
def approve_resource_allocation(
    allocation_id: str,
    actor: str = Body("Provider Dispatcher", embed=True),
    db: Session = Depends(get_db),
):
    """
    Approves a recommended/requested allocation.
    """
    ok, msg, alloc = resource_allocation_service.approve_allocation(db, allocation_id, actor=actor)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    
    return ResourceAllocationResponse(
        id=alloc.id,
        incident_id=alloc.incident_id,
        sos_id=alloc.sos_id,
        resource_id=alloc.resource_id,
        provider_agency_id=alloc.provider_agency_id,
        resource_type=alloc.resource_type,
        requested_quantity=alloc.requested_quantity,
        recommended_quantity=alloc.recommended_quantity,
        allocated_quantity=alloc.allocated_quantity,
        status=alloc.status,
        allocated_by=alloc.allocated_by,
        allocated_at=alloc.allocated_at,
        dispatched_at=alloc.dispatched_at,
        delivered_at=alloc.delivered_at,
        cancelled_at=alloc.cancelled_at,
        notes=alloc.notes,
        created_at=alloc.created_at,
        updated_at=alloc.updated_at,
        resource_name=alloc.resource.name if alloc.resource else alloc.resource_type,
        agency_name=alloc.provider_agency.name if alloc.provider_agency else None,
        unit=alloc.resource.unit if alloc.resource else "Units",
    )

@router.post("/{allocation_id}/dispatch", response_model=ResourceAllocationResponse)
def dispatch_resource_allocation(
    allocation_id: str,
    actor: str = Body("Provider Dispatcher", embed=True),
    notes: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
):
    """
    Transitions allocation to DISPATCHED state with dispatch timestamp.
    """
    ok, msg, alloc = resource_allocation_service.dispatch_allocation(db, allocation_id, actor=actor, notes=notes)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return ResourceAllocationResponse(
        id=alloc.id,
        incident_id=alloc.incident_id,
        sos_id=alloc.sos_id,
        resource_id=alloc.resource_id,
        provider_agency_id=alloc.provider_agency_id,
        resource_type=alloc.resource_type,
        requested_quantity=alloc.requested_quantity,
        recommended_quantity=alloc.recommended_quantity,
        allocated_quantity=alloc.allocated_quantity,
        status=alloc.status,
        allocated_by=alloc.allocated_by,
        allocated_at=alloc.allocated_at,
        dispatched_at=alloc.dispatched_at,
        delivered_at=alloc.delivered_at,
        cancelled_at=alloc.cancelled_at,
        notes=alloc.notes,
        created_at=alloc.created_at,
        updated_at=alloc.updated_at,
        resource_name=alloc.resource.name if alloc.resource else alloc.resource_type,
        agency_name=alloc.provider_agency.name if alloc.provider_agency else None,
        unit=alloc.resource.unit if alloc.resource else "Units",
    )

@router.post("/{allocation_id}/in-transit", response_model=ResourceAllocationResponse)
def mark_resource_in_transit(
    allocation_id: str,
    db: Session = Depends(get_db),
):
    """
    Transitions allocation to IN_TRANSIT state.
    """
    ok, msg, alloc = resource_allocation_service.mark_in_transit(db, allocation_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return ResourceAllocationResponse(
        id=alloc.id,
        incident_id=alloc.incident_id,
        sos_id=alloc.sos_id,
        resource_id=alloc.resource_id,
        provider_agency_id=alloc.provider_agency_id,
        resource_type=alloc.resource_type,
        requested_quantity=alloc.requested_quantity,
        recommended_quantity=alloc.recommended_quantity,
        allocated_quantity=alloc.allocated_quantity,
        status=alloc.status,
        allocated_by=alloc.allocated_by,
        allocated_at=alloc.allocated_at,
        dispatched_at=alloc.dispatched_at,
        delivered_at=alloc.delivered_at,
        cancelled_at=alloc.cancelled_at,
        notes=alloc.notes,
        created_at=alloc.created_at,
        updated_at=alloc.updated_at,
        resource_name=alloc.resource.name if alloc.resource else alloc.resource_type,
        agency_name=alloc.provider_agency.name if alloc.provider_agency else None,
        unit=alloc.resource.unit if alloc.resource else "Units",
    )

@router.post("/{allocation_id}/deliver", response_model=ResourceAllocationResponse)
def mark_resource_delivered(
    allocation_id: str,
    actor: str = Body("Field Agent", embed=True),
    notes: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
):
    """
    Transitions allocation to DELIVERED state upon successful deployment to citizen.
    """
    ok, msg, alloc = resource_allocation_service.mark_delivered(db, allocation_id, actor=actor, notes=notes)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return ResourceAllocationResponse(
        id=alloc.id,
        incident_id=alloc.incident_id,
        sos_id=alloc.sos_id,
        resource_id=alloc.resource_id,
        provider_agency_id=alloc.provider_agency_id,
        resource_type=alloc.resource_type,
        requested_quantity=alloc.requested_quantity,
        recommended_quantity=alloc.recommended_quantity,
        allocated_quantity=alloc.allocated_quantity,
        status=alloc.status,
        allocated_by=alloc.allocated_by,
        allocated_at=alloc.allocated_at,
        dispatched_at=alloc.dispatched_at,
        delivered_at=alloc.delivered_at,
        cancelled_at=alloc.cancelled_at,
        notes=alloc.notes,
        created_at=alloc.created_at,
        updated_at=alloc.updated_at,
        resource_name=alloc.resource.name if alloc.resource else alloc.resource_type,
        agency_name=alloc.provider_agency.name if alloc.provider_agency else None,
        unit=alloc.resource.unit if alloc.resource else "Units",
    )

@router.post("/{allocation_id}/cancel", response_model=ResourceAllocationResponse)
def cancel_resource_allocation(
    allocation_id: str,
    reason: str = Body("Mission redirected or cancelled", embed=True),
    db: Session = Depends(get_db),
):
    """
    Cancels an allocation and immediately restores allocated units back into available inventory.
    """
    ok, msg, alloc = resource_allocation_service.cancel_allocation(db, allocation_id, reason=reason)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return ResourceAllocationResponse(
        id=alloc.id,
        incident_id=alloc.incident_id,
        sos_id=alloc.sos_id,
        resource_id=alloc.resource_id,
        provider_agency_id=alloc.provider_agency_id,
        resource_type=alloc.resource_type,
        requested_quantity=alloc.requested_quantity,
        recommended_quantity=alloc.recommended_quantity,
        allocated_quantity=alloc.allocated_quantity,
        status=alloc.status,
        allocated_by=alloc.allocated_by,
        allocated_at=alloc.allocated_at,
        dispatched_at=alloc.dispatched_at,
        delivered_at=alloc.delivered_at,
        cancelled_at=alloc.cancelled_at,
        notes=alloc.notes,
        created_at=alloc.created_at,
        updated_at=alloc.updated_at,
        resource_name=alloc.resource.name if alloc.resource else alloc.resource_type,
        agency_name=alloc.provider_agency.name if alloc.provider_agency else None,
        unit=alloc.resource.unit if alloc.resource else "Units",
    )
