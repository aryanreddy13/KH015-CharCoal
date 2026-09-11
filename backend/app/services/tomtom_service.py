"""
Bridge / Alias for OpenStreetMap Service.
Provides backwards compatibility for any previous imports.
"""
from app.services.osm_service import (
    OSMService,
    osm_service,
    haversine_distance_km,
)

# Backwards compatible alias
TomTomService = OSMService
tomtom_service = osm_service

__all__ = ["OSMService", "osm_service", "TomTomService", "tomtom_service", "haversine_distance_km"]
