from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import Zone, Resource, Allocation
from app.schemas.schemas import DashboardKPISummary

router = APIRouter(tags=["Health & Summary"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        zones_count = db.query(Zone).count()
        return {
            "status": "healthy",
            "service": "Sanjivini Disaster Response Command Center Backend",
            "phase": "Phase 1 - Foundation & Realtime Core",
            "database_connected": True,
            "zones_count": zones_count,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_connected": False,
        }

@router.get("/summary", response_model=DashboardKPISummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    zones = db.query(Zone).all()
    active_zones = len(zones)
    critical_zones = sum(1 for z in zones if z.status == "Critical" or z.overall_severity >= 9.0)
    total_people = sum(z.affected_people for z in zones)

    available_resources = db.query(Resource).filter(Resource.status == "AVAILABLE").count()
    active_allocations = db.query(Allocation).filter(Allocation.status.in_(["EN_ROUTE", "ALLOCATED", "DELAYED"])).count()

    return DashboardKPISummary(
        active_zones_count=active_zones,
        critical_zones_count=critical_zones,
        available_resources_count=available_resources,
        active_allocations_count=active_allocations,
        total_people_affected=total_people,
    )
