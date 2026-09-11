from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.models import Zone, Need, Allocation, Report, Alert

class ZoneService:
    @staticmethod
    def get_all_zones(db: Session) -> List[Zone]:
        return db.query(Zone).options(joinedload(Zone.needs)).order_by(Zone.overall_severity.desc()).all()

    @staticmethod
    def get_zone_by_id(db: Session, zone_id: str) -> Optional[Zone]:
        return (
            db.query(Zone)
            .options(
                joinedload(Zone.needs),
                joinedload(Zone.allocations).joinedload(Allocation.resource),
                joinedload(Zone.reports),
                joinedload(Zone.alerts),
            )
            .filter(Zone.id == zone_id)
            .first()
        )

    @staticmethod
    def update_zone_severity(db: Session, zone_id: str, severity: float, affected_delta: int = 0) -> Optional[Zone]:
        zone = db.query(Zone).filter(Zone.id == zone_id).first()
        if not zone:
            return None
        zone.overall_severity = round(min(10.0, max(0.0, severity)), 1)
        zone.affected_people += affected_delta
        if zone.overall_severity >= 9.0:
            zone.status = "Critical"
        elif zone.overall_severity >= 7.0:
            zone.status = "High"
        elif zone.overall_severity >= 4.0:
            zone.status = "Moderate"
        else:
            zone.status = "Low"

        db.commit()
        db.refresh(zone)
        return zone

zone_service = ZoneService()
