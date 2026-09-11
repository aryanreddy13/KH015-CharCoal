from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.resource_service import resource_service
from app.schemas.schemas import AllocationResponse

router = APIRouter(prefix="/allocations", tags=["Allocations"])

@router.get("", response_model=List[AllocationResponse])
def list_allocations(db: Session = Depends(get_db)):
    """
    Returns all active and pending resource allocations with status, ETA, and target zones.
    """
    return resource_service.get_all_allocations(db)
