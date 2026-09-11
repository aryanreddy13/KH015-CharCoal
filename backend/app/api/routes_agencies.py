from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import Agency
from app.schemas.schemas import AgencyResponse

router = APIRouter(prefix="/agencies", tags=["Agencies"])

@router.get("", response_model=List[AgencyResponse])
def list_agencies(db: Session = Depends(get_db)):
    """
    Returns registered response agencies (Fire & Rescue, Medical, NGOs, Govt).
    """
    return db.query(Agency).all()
