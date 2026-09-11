from fastapi import APIRouter
from app.api.routes_health import router as health_router
from app.api.routes_zones import router as zones_router
from app.api.routes_resources import router as resources_router
from app.api.routes_needs import router as needs_router
from app.api.routes_allocations import router as allocations_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_audit import router as audit_router
from app.api.routes_reports import router as reports_router
from app.api.routes_agencies import router as agencies_router
from app.api.routes_simulation import router as simulation_router
from app.api.routes_sos import router as sos_router
from app.api.routes_emergency_services import router as emergency_services_router
from app.api.routes_provider import router as provider_router
from app.api.routes_upload import router as upload_router
from app.api.routes_resource_allocation import router as resource_allocation_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(zones_router)
api_router.include_router(resources_router)
api_router.include_router(needs_router)
api_router.include_router(allocations_router)
api_router.include_router(alerts_router)
api_router.include_router(audit_router)
api_router.include_router(reports_router)
api_router.include_router(agencies_router)
api_router.include_router(simulation_router)
api_router.include_router(sos_router)
api_router.include_router(emergency_services_router)
api_router.include_router(provider_router)
api_router.include_router(upload_router)
api_router.include_router(resource_allocation_router)

__all__ = ["api_router"]


