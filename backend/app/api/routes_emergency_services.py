from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import EmergencyServicesResponse, EmergencyServiceItem
from app.services.osm_service import osm_service

router = APIRouter(prefix="/emergency-services", tags=["Emergency Services"])

@router.get("/nearby", response_model=EmergencyServicesResponse)
def get_nearby_services(
    latitude: Optional[float] = Query(None, description="User latitude"),
    longitude: Optional[float] = Query(None, description="User longitude"),
    radius: Optional[float] = Query(None, description="Search radius in meters (e.g. 10000)"),
    radius_km: Optional[float] = Query(None, description="Search radius in kilometers (e.g. 10.0)"),
    type: Optional[str] = Query(None, description="Filter by service type: HOSPITAL, POLICE, FIRE_RESCUE, MEDICAL, NGO, GOVERNMENT"),
    db: Session = Depends(get_db),
):
    """
    Returns verified nearby emergency services (Hospitals, Police, Fire & Rescue, Relief Hubs).
    Uses OpenStreetMap & OSRM Engine to calculate real road distance and driving ETA,
    enriching facilities with registered Supabase provider resource availability.
    """
    # Determine search radius in meters
    radius_meters = 10000
    if radius is not None and radius > 0:
        radius_meters = int(radius)
    elif radius_km is not None and radius_km > 0:
        radius_meters = int(radius_km * 1000)

    # Use OpenStreetMap service with live GPS coordinates if provided
    lat = latitude if latitude is not None else 28.6139
    lon = longitude if longitude is not None else 77.2090

    raw_services = osm_service.get_nearby_emergency_services(
        lat=lat,
        lon=lon,
        radius_meters=radius_meters,
        agency_type_filter=type,
        db=db,
    )

    items: List[EmergencyServiceItem] = []
    for s in raw_services:
        items.append(
            EmergencyServiceItem(
                id=str(s.get("id")),
                name=s.get("name", "Emergency Facility"),
                type=s.get("type", "GOVERNMENT"),
                agency_type=s.get("agency_type", s.get("type")),
                contact_number=s.get("contact_number"),
                phone=s.get("phone"),
                status=s.get("status", "ACTIVE"),
                distance_meters=s.get("distance_meters"),
                distance_km=s.get("distance_km"),
                distance_text=s.get("distance_text"),
                eta_seconds=s.get("eta_seconds"),
                eta_minutes=s.get("eta_minutes"),
                eta_text=s.get("eta_text"),
                latitude=s.get("latitude"),
                longitude=s.get("longitude"),
                address=s.get("address"),
                maps_url=s.get("maps_url"),
                source=s.get("source", "TOMTOM"),
                is_registered_provider=s.get("is_registered_provider", False),
                available_resources=s.get("available_resources"),
            )
        )

    return EmergencyServicesResponse(count=len(items), services=items)

