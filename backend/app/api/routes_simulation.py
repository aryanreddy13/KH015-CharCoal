from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.simulation_service import simulation_service
from app.schemas.schemas import SimulationActionRequest, SimulationActionResponse

router = APIRouter(prefix="/simulation", tags=["Simulation Engine"])

@router.post("/start", response_model=SimulationActionResponse)
async def start_simulation(db: Session = Depends(get_db)):
    """
    Triggers simulated agentic resource movement, telemetry, and live activity events.
    """
    res = await simulation_service.start_simulation(db)
    return SimulationActionResponse(
        success=True,
        message=res.get("message", "Simulation started"),
        event_type="START_SIMULATION",
        details=res,
    )

@router.post("/emergency", response_model=SimulationActionResponse)
async def inject_emergency(req: SimulationActionRequest = None, db: Session = Depends(get_db)):
    """
    Injects sudden severity escalation, victim surge, high-priority emergency report, and alert.
    """
    zone_id = req.zone_id if req else None
    res = await simulation_service.inject_emergency(db, zone_id=zone_id)
    return SimulationActionResponse(
        success=res.get("status") == "success",
        message=f"Emergency surge injected into {res.get('zone', 'Zone')}",
        event_type="INJECT_EMERGENCY",
        details=res,
    )

@router.post("/road-block", response_model=SimulationActionResponse)
async def simulate_road_block(db: Session = Depends(get_db)):
    """
    Simulates arterial route blockage (debris/flooding), delaying convoy and recalculating ETA.
    """
    res = await simulation_service.simulate_road_block(db)
    return SimulationActionResponse(
        success=res.get("status") == "success",
        message=res.get("message", "Road block simulated"),
        event_type="SIMULATE_ROAD_BLOCK",
        details=res,
    )
