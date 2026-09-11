import sys
import os
import unittest
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database.session import SessionLocal, Base, engine
from app.models.models import SOSEvent, Alert, AuditLog, Zone

class TestSOSBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def test_sos_valid_flow(self):
        """
        Verify:
        POST /api/sos
        ↓
        HTTP success (201)
        ↓
        sos_events row created
        ↓
        critical alert created
        ↓
        audit log created
        """
        payload = {
            "reporter_name": "John Doe",
            "contact": "+91-9876543210",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "accuracy": 5.2,
            "description": "Flash flood trapped on rooftop",
            "timestamp": "2026-09-11T08:00:00Z",
        }
        response = self.client.post("/api/sos", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "ACTIVATED")
        self.assertTrue(data["incident_id"].startswith("SOS-"))
        self.assertIn("id", data)
        self.assertEqual(data["reporter_name"], "John Doe")
        self.assertAlmostEqual(data["latitude"], 28.6139)
        self.assertAlmostEqual(data["longitude"], 77.2090)

        sos_id = data["id"]
        incident_id = data["incident_id"]

        # Verify DB entries
        db = SessionLocal()
        try:
            # 1. SOSEvent row
            sos_db = db.query(SOSEvent).filter(SOSEvent.id == sos_id).first()
            self.assertIsNotNone(sos_db)
            self.assertEqual(sos_db.incident_id, incident_id)
            self.assertEqual(sos_db.status, "ACTIVE")
            self.assertEqual(sos_db.contact, "+91-9876543210")

            # 2. Critical Alert created
            alert_db = db.query(Alert).filter(Alert.message.contains(incident_id)).first()
            self.assertIsNotNone(alert_db)
            self.assertEqual(alert_db.alert_level, "CRITICAL")
            self.assertTrue(alert_db.is_active)
            self.assertIn("🚨 SOS ACTIVATED", alert_db.title)

            # 3. Audit Log created
            log_db = db.query(AuditLog).filter(AuditLog.event_type == "SOS_ACTIVATED").order_by(AuditLog.timestamp.desc()).first()
            self.assertIsNotNone(log_db)
            self.assertIn(incident_id, log_db.description)
            self.assertEqual(log_db.status, "CRITICAL")
        finally:
            db.close()

    def test_sos_invalid_coordinates(self):
        """Verify invalid coordinates are rejected with 422 Unprocessable Entity."""
        payload_bad_lat = {
            "reporter_name": "Citizen",
            "latitude": 120.0,  # Invalid (>90)
            "longitude": 77.2090,
        }
        res_lat = self.client.post("/api/sos", json=payload_bad_lat)
        self.assertEqual(res_lat.status_code, 422)

        payload_bad_lng = {
            "reporter_name": "Citizen",
            "latitude": 28.6139,
            "longitude": -200.0,  # Invalid (<-180)
        }
        res_lng = self.client.post("/api/sos", json=payload_bad_lng)
        self.assertEqual(res_lng.status_code, 422)

    def test_get_sos_list(self):
        """Verify GET /api/sos returns beacon list."""
        res = self.client.get("/api/sos")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_emergency_services_nearby(self):
        """Verify GET /api/emergency-services/nearby endpoint."""
        res = self.client.get("/api/emergency-services/nearby?latitude=28.6139&longitude=77.2090")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("count", data)
        self.assertIn("services", data)
        self.assertIsInstance(data["services"], list)

if __name__ == "__main__":
    unittest.main()
