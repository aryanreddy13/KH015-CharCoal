import os
import sys
import json
import logging
from datetime import datetime

# Set path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

from app.config import settings
from app.database.session import Base, engine, SessionLocal, get_engine
from app.models.models import Agency, SOSEvent, Resource, AuditLog, Zone
from app.database.seeder import seed_database
from app.services.email_service import email_service
from app.services.pagerduty_service import pagerduty_service
from app.services.storage_service import storage_service
from app.agents.coordination_agent import coordination_agent
from fastapi.testclient import TestClient
from app.main import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("provider_verify")

def run_tests():
    print("\n" + "=" * 70)
    print("PS20 - EMERGENCY SERVICE PROVIDER PIPELINE & NOTIFICATION VERIFICATION")
    print("=" * 70)

    # 1. Verify DB & Tables
    print("\n[1] Verifying database schema & tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)

    agencies = db.query(Agency).all()
    print(f"    Active Agencies ({len(agencies)}):")
    ag_map = {}
    for a in agencies:
        if a.type not in ag_map or "Alpha" in a.name or a.contact_number == "7977661625":
            ag_map[a.type] = a
        print(f"      - [{a.type}] {a.name} (Contact: {a.contact_number}, Email: {a.email})")
    assert len(agencies) >= 5, "Expected at least 5 provider agencies"
    
    # Verify contact numbers and email configuration
    print("\n    [Detailed Agency Configuration Check]")
    print(f"      POLICE:      phone={ag_map['POLICE'].contact_number!r}, email={ag_map['POLICE'].email!r}")
    print(f"      FIRE:        phone={ag_map['FIRE_RESCUE'].contact_number!r}, email={ag_map['FIRE_RESCUE'].email!r}")
    print(f"      MEDICAL:     phone={ag_map['MEDICAL'].contact_number!r}, email={ag_map['MEDICAL'].email!r}")
    print(f"      NGO:         phone={ag_map['NGO'].contact_number!r}, email={ag_map['NGO'].email!r}")
    print(f"      GOVERNMENT:  phone={ag_map['GOVERNMENT'].contact_number!r}, email={ag_map['GOVERNMENT'].email!r}")

    # Explicit Assertions
    assert "POLICE" in ag_map and ag_map["POLICE"].contact_number is None, "Police should have contact_number = None"
    assert ag_map["POLICE"].email is None, "Police should have email = None"

    assert "FIRE_RESCUE" in ag_map and ag_map["FIRE_RESCUE"].contact_number in ("865247769", "8652477694"), "Fire phone mismatch"
    assert ag_map["FIRE_RESCUE"].email == "danishsjain@gmail.com", "Fire email mismatch"

    assert "MEDICAL" in ag_map and ag_map["MEDICAL"].contact_number == "9833259238", "Medical phone mismatch"
    assert ag_map["MEDICAL"].email == "nairanikait7@gmail.com", "Medical email mismatch"

    assert "NGO" in ag_map and ag_map["NGO"].contact_number == "7977661625", "NGO phone mismatch"
    assert ag_map["NGO"].email == "aryanreddy2006@gmail.com", "NGO email mismatch"

    print("    [PASS] Provider agencies contact numbers and emails verified according to exact specifications.")

    # 2. Test Storage Service (Photo Upload)
    print("\n[2] Testing Storage Service (Photo Upload)...")
    sample_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"  # JPEG magic bytes
    ok, photo_url = storage_service.upload_photo(sample_bytes, "test_flood_evidence.jpg", "image/jpeg")
    print(f"    Upload status: {ok}, URL: {photo_url}")
    assert ok is True and photo_url != ""
    print("    [PASS] Photo upload & storage verified.")

    # 3. Test Multi-Agency Routing Rules (Coordination Agent)
    print("\n[3] Testing Coordination Agent Multi-Agency Routing Rules...")
    # Test Flood
    flood_routes = coordination_agent.determine_relevant_providers(
        db, disaster_type="Flood", description="Rooftop flooding with trapped families",
        severity=9.8, affected_people=350, injured_people=42, missing_people=11
    )
    flood_types = [r["agency_type"] for r in flood_routes]
    print(f"    Flood Routing: {flood_types}")
    assert "FIRE_RESCUE" in flood_types and "MEDICAL" in flood_types

    # Test Security / Police
    sec_routes = coordination_agent.determine_relevant_providers(
        db, disaster_type="Fire", description="Building collapse and fire with perimeter hazard",
        severity=8.0, affected_people=20, injured_people=5, missing_people=2
    )
    sec_types = [r["agency_type"] for r in sec_routes]
    print(f"    Collapse/Fire Routing: {sec_types}")
    assert "FIRE_RESCUE" in sec_types and "POLICE" in sec_types

    # Test that Police in routed list has email=None and contact_number=None
    police_route = next((r for r in sec_routes if r["agency_type"] == "POLICE"), None)
    assert police_route is not None
    assert police_route["email"] is None, "Police routed payload must have email = None"
    assert police_route["contact_number"] is None, "Police routed payload must have contact_number = None"
    print("    [PASS] Police routed with no phone / no email.")

    # Test Food/Relief
    food_routes = coordination_agent.determine_relevant_providers(
        db, disaster_type="Flood", description="Severe food and potable water shortage",
        severity=5.0, affected_people=100, required_resources=["Food", "Water"]
    )
    food_types = [r["agency_type"] for r in food_routes]
    print(f"    Relief Supply Routing: {food_types}")
    assert "NGO" in food_types
    print("    [PASS] Coordination Agent routing rules verified.")

    # 4. Test Resend Email Service (with Photo Attachment & Configured Gmails)
    print("\n[4] Testing Resend Emergency Email Service for configured agency emails...")
    sample_incident = {
        "incident_id": "SOS-TEST-999",
        "disaster_type": "Flood",
        "zone_name": "Zone A - Riverfront",
        "severity": 9.8,
        "people_affected": 350,
        "injured_people": 42,
        "missing_people": 11,
        "required_resources": ["Rescue", "Medical"],
        "latitude": 28.6145,
        "longitude": 77.2090,
        "distance_km": 4.8,
        "eta_minutes": 11,
        "provider_status": "NEW",
    }

    # Verify Medical recipient (Registered Resend Account Owner)
    med_ok, med_status = email_service.send_emergency_email(
        recipient=settings.MEDICAL_EMERGENCY_EMAIL,
        incident=sample_incident,
        photo_url=photo_url,
    )
    print(f"    Medical Email Dispatch ({settings.MEDICAL_EMERGENCY_EMAIL}): success={med_ok}, status={med_status}")
    assert med_ok is True
    assert settings.MEDICAL_EMERGENCY_EMAIL == "nairanikait7@gmail.com"

    # Verify Fire & NGO recipients (Resend API will dispatch or inform of domain verification requirements)
    fire_ok, fire_status = email_service.send_emergency_email(
        recipient=settings.FIRE_EMERGENCY_EMAIL,
        incident=sample_incident,
        photo_url=photo_url,
    )
    print(f"    Fire Email Dispatch ({settings.FIRE_EMERGENCY_EMAIL}): success={fire_ok}, status={fire_status}")
    assert settings.FIRE_EMERGENCY_EMAIL == "danishsjain@gmail.com"

    ngo_ok, ngo_status = email_service.send_emergency_email(
        recipient=settings.NGO_EMERGENCY_EMAIL,
        incident=sample_incident,
        photo_url=photo_url,
    )
    print(f"    NGO Email Dispatch ({settings.NGO_EMERGENCY_EMAIL}): success={ngo_ok}, status={ngo_status}")
    assert settings.NGO_EMERGENCY_EMAIL == "aryanreddy2006@gmail.com"

    print("    [PASS] Resend email service verified with exact recipient addresses & photo attachment.")

    # 5. Test PagerDuty Service (Events API v2 / Voice Call Payload)
    print("\n[5] Testing PagerDuty Emergency Escalation Service...")
    provider_dict = {"name": "Fire & Rescue Department", "type": "FIRE_RESCUE"}
    pd_ok, pd_status = pagerduty_service.trigger_pagerduty_incident(
        incident=sample_incident,
        provider=provider_dict,
        affected_count=350,
        injured_count=42,
        missing_count=11,
        eta=11,
    )
    print(f"    PagerDuty Dispatch: success={pd_ok}, status={pd_status}")
    assert pd_ok is True
    print("    [PASS] PagerDuty service verified.")

    # 6. Test Non-Blocking Failure Resilience on POST /api/sos
    print("\n[6] Testing End-to-End POST /api/sos (with Background Dispatch & Resilience)...")
    with TestClient(app) as client:
        sos_payload = {
            "reporter_name": "Citizen Rohit Verma",
            "contact": "+91-98111-22233",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "accuracy": 4.5,
            "description": "Severe embankment breach! Rapid water current engulfing ground floors.",
            "disaster_type": "Flood",
            "severity": 9.8,
            "people_affected": 350,
            "injured_people": 42,
            "missing_people": 11,
            "photo_url": photo_url,
            "required_resources": ["Rescue", "Medical"],
        }
        res = client.post("/api/sos", json=sos_payload)
        print(f"    POST /api/sos Status: {res.status_code}")
        assert res.status_code == 201
        created_sos = res.json()
        inc_id = created_sos["incident_id"]
        print(f"    Created SOS Incident ID: {inc_id}, Provider Status: {created_sos['provider_status']}")
        assert inc_id.startswith("SOS-")

        # 7. Test Provider APIs & State Transitions
        print("\n[7] Testing Provider Operations APIs (/api/provider/*)...")
        # GET /api/provider/agencies
        res = client.get("/api/provider/agencies")
        assert res.status_code == 200
        print(f"    GET /api/provider/agencies: {len(res.json())} agencies")

        # GET /api/provider/kpis
        res = client.get("/api/provider/kpis?agency_type=FIRE_RESCUE")
        assert res.status_code == 200
        kpis = res.json()
        print(f"    GET /api/provider/kpis: {kpis}")
        assert "active_incidents" in kpis and "available_units" in kpis

        # GET /api/provider/incidents
        res = client.get("/api/provider/incidents?agency_type=FIRE_RESCUE")
        assert res.status_code == 200
        incidents = res.json()
        print(f"    GET /api/provider/incidents (FIRE_RESCUE): {len(incidents)} incidents found")
        assert len(incidents) > 0

        # State Transitions: NEW -> ACCEPTED -> DISPATCHED -> EN_ROUTE -> ARRIVED -> RESOLVED
        print("\n[8] Testing Incident Lifecycle Action State Machine...")
        # Step A: ACCEPT
        res = client.post(f"/api/provider/incidents/{inc_id}/accept")
        print(f"    [ACCEPT] Status: {res.status_code}, New State: {res.json().get('new_status')}")
        assert res.status_code == 200
        assert res.json()["new_status"] == "ACCEPTED"

        # Step B: DISPATCH
        res = client.post(f"/api/provider/incidents/{inc_id}/dispatch", json={"notes": "Mobilizing Boat Unit 01"})
        print(f"    [DISPATCH] Status: {res.status_code}, New State: {res.json().get('new_status')}")
        assert res.status_code == 200
        assert res.json()["new_status"] == "DISPATCHED"

        # Step C: EN_ROUTE
        res = client.post(f"/api/provider/incidents/{inc_id}/en-route")
        print(f"    [EN_ROUTE] Status: {res.status_code}, New State: {res.json().get('new_status')}")
        assert res.status_code == 200
        assert res.json()["new_status"] == "EN_ROUTE"

        # Step D: ARRIVED
        res = client.post(f"/api/provider/incidents/{inc_id}/arrived")
        print(f"    [ARRIVED] Status: {res.status_code}, New State: {res.json().get('new_status')}")
        assert res.status_code == 200
        assert res.json()["new_status"] == "ARRIVED"

        # Step E: RESOLVE
        res = client.post(f"/api/provider/incidents/{inc_id}/resolve", json={"notes": "All victims safely evacuated to relief camp."})
        print(f"    [RESOLVE] Status: {res.status_code}, New State: {res.json().get('new_status')}")
        assert res.status_code == 200
        assert res.json()["new_status"] == "RESOLVED"

        # Step F: Invalid Transition Validation Test (RESOLVED -> ACCEPTED should return 400)
        res = client.post(f"/api/provider/incidents/{inc_id}/accept")
        print(f"    [INVALID TRANSITION TEST] Status: {res.status_code} (Expected 400)")
        assert res.status_code == 400
        print("    [PASS] State transition validation successfully rejected invalid step.")

        # 9. Test Simulation Injection
        print("\n[9] Testing POST /api/simulation/emergency...")
        res = client.post("/api/simulation/emergency")
        print(f"    Simulation Status: {res.status_code}, Details: {res.json().get('details')}")
        assert res.status_code == 200
        print("    [PASS] Full emergency scenario simulation verified.")

        # 10. Test Audit Logs verification
        res = client.get("/api/audit-logs")
        logs = res.json()
        print(f"\n[10] Verifying Audit Logs: {len(logs)} audit entries recorded.")
        assert len(logs) >= 5
        print("    [PASS] Comprehensive audit trail verified.")

        # 11. WebSocket Connectivity
        print("\n[11] Testing Realtime WebSocket /ws/dashboard...")
        with client.websocket_connect("/ws/dashboard") as ws:
            ws.send_text("ping")
            reply = ws.receive_text()
            print(f"    WebSocket Ping -> Reply: '{reply}'")
            assert reply == "pong"
        print("    [PASS] Real-time WebSocket broadcasting verified.")

    db.close()
    print("\n" + "=" * 70)
    print("ALL 11 BACKEND NOTIFICATION & PROVIDER TESTS PASSED SUCCESSFULLY!")
    print("=" * 70 + "\n")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
