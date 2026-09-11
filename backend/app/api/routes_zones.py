from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.zone_service import zone_service
from app.schemas.schemas import ZoneResponse, ZoneDetailResponse

router = APIRouter(prefix="/zones", tags=["Zones"])

@router.get("", response_model=List[ZoneResponse])
def list_zones(db: Session = Depends(get_db)):
    """
    Returns all 5 disaster response zones along with current requirement needs.
    """
    return zone_service.get_all_zones(db)

@router.get("/{zone_id}", response_model=ZoneDetailResponse)
def get_zone(zone_id: str, db: Session = Depends(get_db)):
    """
    Returns comprehensive details for a specific zone: needs, active allocations, reports, alerts.
    """
    zone = zone_service.get_zone_by_id(db, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Disaster zone not found")
    return zone
