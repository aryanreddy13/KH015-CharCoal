import os
import sys
import logging
from datetime import datetime

# Set working path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.database.session import Base, get_engine, SessionLocal, mask_db_url
from app.models.models import (
    User, Agency, Zone, Report, ReportUpdate, Need,
    Resource, ResourceLocation, Allocation, Alert, AuditLog, SOSEvent
)
from app.database.seeder import seed_database
from fastapi.testclient import TestClient
from app.main import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("supabase_verify")

def run_migration_and_verification():
    print("\n" + "=" * 60)
    print("PS20 DISASTER PLATFORM - SUPABASE POSTGRESQL MIGRATION & TEST")
    print("=" * 60)

    # 1. Test Direct Connection
    db_url = settings.DATABASE_URL
    masked = mask_db_url(db_url)
    print(f"\n[1] Testing connection to configured DATABASE_URL ({masked})...")

    engine = get_engine()
    dialect = engine.dialect.name
    print(f"    Active Dialect: {dialect.upper()}")
    
    if dialect == "sqlite":
        print("    [WARNING] Engine is using SQLite fallback! Check connection URL/credentials.")
    else:
        print("    [SUCCESS] Direct connection to Supabase PostgreSQL established.")

    # 2. Create Schema / Tables
    print("\n[2] Creating / Verifying 12 tables in database...")
    Base.metadata.create_all(bind=engine)
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    created_tables = inspector.get_table_names()
    expected_tables = [
        "users", "agencies", "zones", "reports", "report_updates",
        "needs", "resources", "resource_locations", "allocations",
        "alerts", "audit_logs", "sos_events"
    ]
    
    all_found = True
    for table in expected_tables:
        exists = table in created_tables
        status = "OK" if exists else "MISSING"
        print(f"    - Table '{table}': {status}")
        if not exists:
            all_found = False

    if not all_found:
        print("    [ERROR] Some tables are missing in the schema.")
        return False
    print("    [SUCCESS] All 12 tables verified in schema.")

    # 3. Seed Database
    print("\n[3] Running seeder...")
    db = SessionLocal()
    try:
        seed_database(db)
        print("    [SUCCESS] Seed process executed successfully.")
    except Exception as e:
        print(f"    [ERROR] Seed process failed: {e}")
        db.close()
        return False

    # 4. Verify Record Counts
    print("\n[4] Verifying database records...")
    zone_count = db.query(Zone).count()
    agency_count = db.query(Agency).count()
    resource_count = db.query(Resource).count()
    need_count = db.query(Need).count()
    allocation_count = db.query(Allocation).count()
    alert_count = db.query(Alert).count()
    report_count = db.query(Report).count()
    audit_count = db.query(AuditLog).count()
    user_count = db.query(User).count()
    sos_count = db.query(SOSEvent).count()

    print(f"    - Zones count: {zone_count} (Expected: 5)")
    print(f"    - Agencies count: {agency_count} (Expected: 5)")
    print(f"    - Resources count: {resource_count} (Expected: 12)")
    print(f"    - Needs count: {need_count} (Expected: 11)")
    print(f"    - Allocations count: {allocation_count} (Expected: 4)")
    print(f"    - Alerts count: {alert_count} (Expected: 4)")
    print(f"    - Reports count: {report_count} (Expected: >=2)")
    print(f"    - Audit Logs count: {audit_count} (Expected: >=5)")
    print(f"    - Users count: {user_count} (Expected: >=1)")
    print(f"    - SOS Events count: {sos_count}")

    zones = db.query(Zone).order_by(Zone.name).all()
    print("    Zones loaded:")
    for z in zones:
        print(f"      * {z.name} (Type: {z.disaster_type}, Severity: {z.overall_severity}, Affected: {z.affected_people})")

    db.close()

    # 5. Test REST Endpoints via TestClient
    print("\n[5] Testing REST API Endpoints...")
    with TestClient(app) as client:
        # GET /api/health
        res = client.get("/api/health")
        print(f"    GET /api/health -> Status {res.status_code}, Payload: {res.json()}")
        assert res.status_code == 200
        assert res.json().get("database_connected") is True

        # GET /api/zones
        res = client.get("/api/zones")
        print(f"    GET /api/zones -> Status {res.status_code}, Zones count: {len(res.json())}")
        assert res.status_code == 200
        assert len(res.json()) == 5

        # GET /api/resources
        res = client.get("/api/resources")
        print(f"    GET /api/resources -> Status {res.status_code}, Resources count: {len(res.json())}")
        assert res.status_code == 200

        # GET /api/needs
        res = client.get("/api/needs")
        print(f"    GET /api/needs -> Status {res.status_code}, Needs count: {len(res.json())}")
        assert res.status_code == 200

        # GET /api/allocations
        res = client.get("/api/allocations")
        print(f"    GET /api/allocations -> Status {res.status_code}, Allocations count: {len(res.json())}")
        assert res.status_code == 200

        # GET /api/alerts
        res = client.get("/api/alerts")
        print(f"    GET /api/alerts -> Status {res.status_code}, Alerts count: {len(res.json())}")
        assert res.status_code == 200

        # GET /api/reports
        res = client.get("/api/reports")
        print(f"    GET /api/reports -> Status {res.status_code}, Reports count: {len(res.json())}")
        assert res.status_code == 200

        # GET /api/audit-logs
        res = client.get("/api/audit-logs")
        print(f"    GET /api/audit-logs -> Status {res.status_code}, Audit Logs count: {len(res.json())}")
        assert res.status_code == 200

        # 6. Test POST /api/sos
        print("\n[6] Testing POST /api/sos...")
        sos_payload = {
            "latitude": 28.6145,
            "longitude": 77.2090,
            "accuracy": 5.0,
            "reporter_name": "Test Citizen Supabase",
            "contact": "+91-9999999999",
            "description": "Supabase migration test emergency signal",
        }
        res = client.post("/api/sos", json=sos_payload)
        print(f"    POST /api/sos -> Status {res.status_code}, Response: {res.json()}")
        assert res.status_code == 201
        created_sos = res.json()
        assert "incident_id" in created_sos

        # Verify SOS was saved in DB
        db_check = SessionLocal()
        sos_row = db_check.query(SOSEvent).filter(SOSEvent.id == created_sos["id"]).first()
        assert sos_row is not None
        print(f"    [SUCCESS] SOS record successfully verified in database (ID: {sos_row.id}, Incident: {sos_row.incident_id})")
        db_check.close()

        # 7. Test WebSocket
        print("\n[7] Testing WebSocket /ws/dashboard...")
        with client.websocket_connect("/ws/dashboard") as websocket:
            websocket.send_text("ping")
            reply = websocket.receive_text()
            print(f"    WebSocket ping -> response: '{reply}'")
            assert reply == "pong"
        print("    [SUCCESS] WebSocket connected and responded correctly.")

    print("\n" + "=" * 60)
    print("ALL SUPABASE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60 + "\n")
    return True

if __name__ == "__main__":
    success = run_migration_and_verification()
    sys.exit(0 if success else 1)
