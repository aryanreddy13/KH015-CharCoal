from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.models import Resource, Allocation, Need

class ResourceService:
    @staticmethod
    def get_all_resources(db: Session) -> List[Resource]:
        return db.query(Resource).options(joinedload(Resource.agency)).all()

    @staticmethod
    def get_resource_by_id(db: Session, resource_id: str) -> Optional[Resource]:
        return db.query(Resource).options(joinedload(Resource.agency)).filter(Resource.id == resource_id).first()

    @staticmethod
    def update_resource_status(db: Session, resource_id: str, status: str) -> Optional[Resource]:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            return None
        resource.status = status
        db.commit()
        db.refresh(resource)
        return resource

    @staticmethod
    def get_all_allocations(db: Session) -> List[Allocation]:
        return (
            db.query(Allocation)
            .options(
                joinedload(Allocation.resource).joinedload(Resource.agency),
                joinedload(Allocation.zone),
                joinedload(Allocation.need),
            )
            .order_by(Allocation.allocated_at.desc())
            .all()
        )

    @staticmethod
    def get_all_needs(db: Session) -> List[Need]:
        return db.query(Need).order_by(Need.priority_score.desc()).all()

resource_service = ResourceService()
