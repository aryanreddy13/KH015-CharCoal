from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.resource_service import resource_service
from app.schemas.schemas import NeedResponse

router = APIRouter(prefix="/needs", tags=["Needs"])

@router.get("", response_model=List[NeedResponse])
def list_needs(db: Session = Depends(get_db)):
    """
    Returns individual critical resource needs ranked by priority score and severity.
    """
    return resource_service.get_all_needs(db)
