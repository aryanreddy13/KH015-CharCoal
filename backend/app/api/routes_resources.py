from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.resource_service import resource_service
from app.schemas.schemas import ResourceResponse

router = APIRouter(prefix="/resources", tags=["Resources"])

@router.get("", response_model=List[ResourceResponse])
def list_resources(db: Session = Depends(get_db)):
    """
    Returns full resource inventory across all emergency agencies.
    """
    return resource_service.get_all_resources(db)

@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(resource_id: str, db: Session = Depends(get_db)):
    """
    Returns specific resource status, location, and capacity.
    """
    resource = resource_service.get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource
