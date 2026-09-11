"""
Comprehensive Verification Suite for OpenStreetMap (OSM) & OSRM Emergency Services
Tests:
1. OpenStreetMap Service Configuration & Endpoints
2. OSRM Road Distance & Driving ETA Calculations
3. Dynamic POI Discovery across multiple GPS Coordinates (Delhi vs Mumbai)
4. Strict Police Policy (No phone calls, contact_number = None)
5. Decision Engine: Nearest Registered Provider WITH available inventory (available_quantity > 0)
6. REST API Endpoint (/api/emergency-services/nearby)
7. End-to-End SOS Creation with OSM/OSRM Road Distance & Driving ETA
"""
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
# Ensure UTF-8 stdout for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.models.models import Agency, Resource, SOSEvent, ResourceAllocation
from app.services.osm_service import osm_service, haversine_distance_km
from app.services.sos_service import SOSService
from app.schemas.schemas import SOSCreate


def run_osm_verification():
    print("=" * 70)
    print("PS20 OPENSTREETMAP (OSM) & OSRM REAL-TIME EMERGENCY SERVICES VERIFICATION")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Step 1: Verify OSM Service Configuration
        print("\n--- STEP 1: OpenStreetMap Service Initialization & Configuration ---")
        print(f"OSM Map Tile URL: {osm_service.tile_url}")
        print(f"OSRM Routing URL: {osm_service.osrm_url}")
        print(f"OSM Nominatim URL: {osm_service.nominatim_url}")
        assert "tile.openstreetmap.org" in osm_service.tile_url
        assert "router.project-osrm.org" in osm_service.osrm_url or "route/v1/driving" in osm_service.osrm_url
        print("[PASS] OpenStreetMap service initialization verified.")

        # Step 2: Test OSRM Routing Engine
        print("\n--- STEP 2: Testing OSRM Real Road Distance & Travel Duration ---")
        loc1 = (28.6139, 77.2090) # India Gate
        loc2 = (28.6304, 77.2177) # Connaught Place
        route_res = osm_service.calculate_route(loc1[0], loc1[1], loc2[0], loc2[1])
        print(f"Route Loc1 -> Loc2: {route_res}")
        assert route_res is not None
        assert "distance_meters" in route_res and route_res["distance_meters"] > 0
        assert "distance_km" in route_res and route_res["distance_km"] > 0
        assert "eta_seconds" in route_res and route_res["eta_seconds"] > 0
        assert "eta_minutes" in route_res and route_res["eta_minutes"] > 0
        assert "ETA ~" in route_res["eta_text"]
        print(f"[PASS] OSRM calculate_route returned: {route_res['distance_text']}, {route_res['eta_text']} (source: {route_res['source']})")

        # Step 3: Test Dynamic POI Discovery across 2 different GPS locations
        print("\n--- STEP 3: Testing Dynamic POI Discovery (Delhi vs Mumbai GPS Coordinates) ---")
        delhi_coords = (28.6139, 77.2090)
        mumbai_coords = (18.9220, 72.8347)

        services_delhi = osm_service.get_nearby_emergency_services(delhi_coords[0], delhi_coords[1], radius_meters=15000, db=db)
        services_mumbai = osm_service.get_nearby_emergency_services(mumbai_coords[0], mumbai_coords[1], radius_meters=15000, db=db)

        print(f"Discovered {len(services_delhi)} services near Delhi coordinates.")
        print(f"Discovered {len(services_mumbai)} services near Mumbai coordinates.")

        assert len(services_delhi) > 0, "Expected at least 1 service near Delhi"
        assert len(services_mumbai) > 0, "Expected at least 1 service near Mumbai"

        delhi_top = services_delhi[0]
        mumbai_top = services_mumbai[0]
        print(f"Delhi Top Result: {delhi_top['name']} ({delhi_top['agency_type']}) - {delhi_top['distance_text']} - {delhi_top['eta_text']}")
        print(f"Mumbai Top Result: {mumbai_top['name']} ({mumbai_top['agency_type']}) - {mumbai_top['distance_text']} - {mumbai_top['eta_text']}")

        # Confirm facilities, distances, and coordinates actually differ across distinct locations
        assert (delhi_top["latitude"], delhi_top["longitude"]) != (mumbai_top["latitude"], mumbai_top["longitude"]), "Delhi and Mumbai locations must have distinct coordinates"
        print("[PASS] Multi-location GPS differentiation verified.")

        # Step 4: Strict Police Contact Policy
        print("\n--- STEP 4: Verifying Police Phone Contact Policy ---")
        police_facilities = [s for s in services_delhi if s["agency_type"] == "POLICE"]
        for pf in police_facilities:
            print(f"Police facility: {pf['name']} | contact_number: {pf.get('contact_number')}")
            assert pf.get("contact_number") is None, "Police contact_number must be None to prevent automatic phone calls."
        print("[PASS] Police policy verified: No automated phone calls configured.")

        # Step 5: Test Decision Engine (Supabase Stock Availability Priority)
        print("\n--- STEP 5: Testing Decision Engine (OSM Proximity + Supabase Stock Availability) ---")
        # Ensure Provider matching prioritizes providers with available_quantity > 0 over depleted ones
        user_lat, user_lon = 28.6139, 77.2090
        
        # Test Medical / Ambulance matching
        med_agency, med_res, dist_km, eta_min = osm_service.match_best_provider_with_inventory(
            db=db,
            lat=user_lat,
            lon=user_lon,
            resource_type="AMBULANCE",
            required_qty=1
        )
        print(f"Selected Medical Provider: {med_agency.name if med_agency else 'None'} | Resource: {med_res.name if med_res else 'None'}")
        print(f"Available Stock: {med_res.available_quantity if med_res else 0} | Distance: {dist_km} km | ETA: {eta_min} min")
        assert med_agency is not None
        assert med_res is not None
        assert (med_res.available_quantity or 0) > 0, "Selected provider must have available stock > 0"

        # Test Fire Rescue matching
        fire_agency, fire_res, f_dist, f_eta = osm_service.match_best_provider_with_inventory(
            db=db,
            lat=user_lat,
            lon=user_lon,
            resource_type="RESCUE",
            required_qty=1
        )
        print(f"Selected Fire Provider: {fire_agency.name if fire_agency else 'None'} | Resource: {fire_res.name if fire_res else 'None'}")
        print(f"Available Stock: {fire_res.available_quantity if fire_res else 0} | Distance: {f_dist} km | ETA: {f_eta} min")
        assert fire_agency is not None
        assert fire_res is not None
        assert (fire_res.available_quantity or 0) > 0, "Selected fire provider must have available stock > 0"
        print("[PASS] Decision engine provider inventory matching verified.")

        # Step 6: Test REST API Endpoint directly
        print("\n--- STEP 6: Testing GET /api/emergency-services/nearby REST Endpoint ---")
        from app.api.routes_emergency_services import get_nearby_services
        api_res = get_nearby_services(
            latitude=28.6139,
            longitude=77.2090,
            radius=10000,
            type=None,
            db=db
        )
        print(f"API Returned {api_res.count} facilities.")
        assert api_res.count > 0
        for item in api_res.services[:3]:
            print(f"- [{item.agency_type}] {item.name} | {item.distance_text} | {item.eta_text} | Source: {item.source}")
            assert item.distance_text is not None and len(item.distance_text) > 0
            assert item.eta_text is not None and len(item.eta_text) > 0
            assert item.maps_url is not None and "http" in item.maps_url
        print("[PASS] REST API endpoint output contract verified.")

        # Step 7: End-to-End SOS Creation with OpenStreetMap / OSRM Routing
        print("\n--- STEP 7: Testing End-to-End SOS Creation with OSM/OSRM Routing ---")
        sos_input = SOSCreate(
            reporter_name="OSM Test Citizen",
            contact="7977661625",
            latitude=28.6289,
            longitude=77.2065,
            disaster_type="Flood",
            severity=8.5,
            description="Testing real-time emergency routing with OpenStreetMap and OSRM engine.",
            food_required=True,
            food_quantity=30,
            water_required=True,
            water_quantity=50,
            ambulance_required=True,
            ambulances_required=1,
            rescue_required=True,
            rescue_units_required=2
        )

        sos_event, alert, log = SOSService.create_sos(db, sos_input)
        print(f"Created Incident: {sos_event.incident_id}")
        print(f"Alert ID: {alert.id} | Status: {alert.alert_level}")

        assert sos_event.distance_km is not None and sos_event.distance_km > 0
        assert sos_event.eta_minutes is not None and sos_event.eta_minutes > 0
        print("[PASS] End-to-end SOS creation with OSM/OSRM routing validated.")

        print("\n" + "=" * 70)
        print(">>> ALL OPENSTREETMAP (OSM) & OSRM REAL-TIME SERVICES TESTS PASSED! <<<")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    run_osm_verification()
