"""
Automated Test Suite for PS20 Need & Assessment Agent
Tests all 12 Required Test Cases:
1. TEST 1 — Detailed Report (Form fields)
2. TEST 2 — Description Extraction (disaster_type, trapped)
3. TEST 3 — SOS One-Tap (GPS only, unknown fields null, zero LLM calls)
4. TEST 4 — No Hallucination ("fire nearby", counts stay null)
5. TEST 5 — Explicit Form Value Wins (Form authoritative precedence)
6. TEST 6 — Negative Number Handling (Validation / normalization)
7. TEST 7 — LLM Failure Fallback (Deterministic fallback)
8. TEST 8 — Invalid LLM JSON (Malformed JSON recovery)
9. TEST 9 — Explicit Resource Quantity ("water for 20", no calculations)
10. TEST 10 — Urgency Extraction (Urgency keywords, no severity)
11. TEST 11 — Unknown Values (Strict null preservation)
12. TEST 12 — Conflicting Information (Form disaster wins, description in facts)
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Configure UTF-8 stdout for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.agents.need_assessment_agent import need_assessment_agent, NeedAssessmentAgent
from app.schemas.schemas import SOSCreate, ReportCreate, IncidentAssessment
from app.services.sos_service import sos_service
from app.services.report_service import report_service


def run_all_tests():
    print("=" * 70)
    print("PS20 NEED & ASSESSMENT AGENT VERIFICATION SUITE")
    print("=" * 70)

    agent = NeedAssessmentAgent()

    # -------------------------------------------------------------
    # TEST 1 — Detailed Report (Form fields)
    # -------------------------------------------------------------
    print("\n--- TEST 1: Detailed Report (Form Inputs) ---")
    data_1 = {
        "incident_id": "TEST-01",
        "input_mode": "REPORT",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "disaster_type": "FLOOD",
        "people_affected": 10,
        "people_injured": 2,
        "people_trapped": 5,
        "description": "Flood water surrounding ground floor.",
    }
    res_1 = agent.assess_incident(data_1, input_mode="REPORT")
    print(f"Result: disaster={res_1.disaster.type}, affected={res_1.people.affected.value}, injured={res_1.people.injured.value}, trapped={res_1.people.trapped.value}")
    assert res_1.disaster.type == "FLOOD"
    assert res_1.disaster.source == "USER_FORM"
    assert res_1.people.affected.value == 10
    assert res_1.people.affected.source == "USER_FORM"
    assert res_1.people.injured.value == 2
    assert res_1.people.injured.source == "USER_FORM"
    assert res_1.people.trapped.value == 5
    assert res_1.people.trapped.source == "USER_FORM"
    assert res_1.people.missing.value is None
    assert res_1.people.missing.source == "UNKNOWN"
    print("[PASS] Test 1: Detailed report form inputs validated.")

    # -------------------------------------------------------------
    # TEST 2 — Description Extraction
    # -------------------------------------------------------------
    print("\n--- TEST 2: Description Extraction ---")
    data_2 = {
        "incident_id": "TEST-02",
        "input_mode": "REPORT",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "description": "Flood water has entered the house and three people are trapped.",
    }
    res_2 = agent.assess_incident(data_2, input_mode="REPORT")
    print(f"Result: disaster={res_2.disaster.type}, trapped={res_2.people.trapped.value}, facts={res_2.facts}")
    assert res_2.disaster.type == "FLOOD"
    assert res_2.people.trapped.value == 3
    print("[PASS] Test 2: Description extraction (disaster & trapped count) validated.")

    # -------------------------------------------------------------
    # TEST 3 — SOS One-Tap
    # -------------------------------------------------------------
    print("\n--- TEST 3: SOS One-Tap (GPS Only) ---")
    data_3 = {
        "incident_id": "TEST-03",
        "input_mode": "SOS",
        "latitude": 19.0760,
        "longitude": 72.8777,
    }
    # Track that no OpenAI call is made
    with patch("app.services.openai_service.OpenAIService.extract_incident_data") as mock_openai:
        res_3 = agent.assess_incident(data_3, input_mode="SOS")
        mock_openai.assert_not_called()

    print(f"Result: input_mode={res_3.input_mode}, disaster={res_3.disaster.type}, people={res_3.people.model_dump()}")
    assert res_3.input_mode == "SOS"
    assert res_3.disaster.type is None
    assert res_3.people.affected.value is None
    assert res_3.people.injured.value is None
    assert res_3.people.trapped.value is None
    assert res_3.people.missing.value is None
    assert res_3.people.casualties.value is None
    assert res_3.extraction_metadata.source == "SYSTEM"
    print("[PASS] Test 3: SOS One-Tap verified (zero LLM calls, null unknown fields).")

    # -------------------------------------------------------------
    # TEST 4 — No Hallucination
    # -------------------------------------------------------------
    print("\n--- TEST 4: No Hallucination ---")
    data_4 = {
        "incident_id": "TEST-04",
        "input_mode": "REPORT",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "description": "There is a fire nearby.",
    }
    res_4 = agent.assess_incident(data_4, input_mode="REPORT")
    print(f"Result: disaster={res_4.disaster.type}, affected={res_4.people.affected.value}, injured={res_4.people.injured.value}")
    assert res_4.disaster.type == "FIRE"
    assert res_4.people.affected.value is None
    assert res_4.people.injured.value is None
    assert res_4.people.trapped.value is None
    print("[PASS] Test 4: No hallucination verified (non-mentioned counts remain null).")

    # -------------------------------------------------------------
    # TEST 5 — Explicit Form Value Wins
    # -------------------------------------------------------------
    print("\n--- TEST 5: Explicit Form Value Wins ---")
    data_5 = {
        "incident_id": "TEST-05",
        "input_mode": "REPORT",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "people_injured": 3,
        "description": "Several people are hurt.",
    }
    res_5 = agent.assess_incident(data_5, input_mode="REPORT")
    print(f"Result: injured={res_5.people.injured.value}, source={res_5.people.injured.source}")
    assert res_5.people.injured.value == 3
    assert res_5.people.injured.source == "USER_FORM"
    print("[PASS] Test 5: Authoritative form precedence verified.")

    # -------------------------------------------------------------
    # TEST 6 — Negative Number
    # -------------------------------------------------------------
    print("\n--- TEST 6: Negative Number Handling ---")
    data_6 = {
        "incident_id": "TEST-06",
        "input_mode": "REPORT",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "people_injured": -4,
        "description": "Minor damage reported.",
    }
    res_6 = agent.assess_incident(data_6, input_mode="REPORT")
    print(f"Result: injured={res_6.people.injured.value}")
    assert res_6.people.injured.value is None
    assert res_6.people.injured.source == "UNKNOWN"
    print("[PASS] Test 6: Negative number safely normalized to null.")

    # -------------------------------------------------------------
    # TEST 7 — LLM Failure Fallback
    # -------------------------------------------------------------
    print("\n--- TEST 7: LLM Failure Fallback ---")
    data_7 = {
        "incident_id": "TEST-07",
        "input_mode": "REPORT",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "description": "Severe earthquake struck, 4 people are trapped under debris.",
    }
    with patch("app.services.openai_service.OpenAIService.extract_incident_data", side_effect=Exception("OpenAI Offline")):
        res_7 = agent.assess_incident(data_7, input_mode="REPORT")

    print(f"Result: disaster={res_7.disaster.type}, trapped={res_7.people.trapped.value}, source={res_7.extraction_metadata.source}")
    assert res_7.disaster.type == "EARTHQUAKE"
    assert res_7.people.trapped.value == 4
    assert res_7.extraction_metadata.source == "DETERMINISTIC_FALLBACK"
    print("[PASS] Test 7: Deterministic fallback on LLM failure verified.")

    # -------------------------------------------------------------
    # TEST 8 — Invalid LLM JSON
    # -------------------------------------------------------------
    print("\n--- TEST 8: Invalid LLM JSON ---")
    data_8 = {
        "incident_id": "TEST-08",
        "input_mode": "REPORT",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "description": "Cyclone winds tearing roofs, 2 people are injured.",
    }
    with patch("app.services.openai_service.OpenAIService.extract_incident_data", return_value="INVALID_NOT_A_DICT"):
        res_8 = agent.assess_incident(data_8, input_mode="REPORT")

    print(f"Result: disaster={res_8.disaster.type}, injured={res_8.people.injured.value}, source={res_8.extraction_metadata.source}")
    assert res_8.disaster.type == "CYCLONE"
    assert res_8.people.injured.value == 2
    assert res_8.extraction_metadata.source == "DETERMINISTIC_FALLBACK"
    print("[PASS] Test 8: Malformed LLM output handled safely via fallback.")

    # -------------------------------------------------------------
    # TEST 9 — Explicit Resource Quantity
    # -------------------------------------------------------------
    print("\n--- TEST 9: Explicit Resource Quantity ---")
    data_9 = {
        "incident_id": "TEST-09",
        "input_mode": "REPORT",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "description": "We need water for 20 people and food for 15.",
    }
    res_9 = agent.assess_incident(data_9, input_mode="REPORT")
    print(f"Result: needs={res_9.needs}, requests={[r.model_dump() for r in res_9.explicit_requests]}")
    assert res_9.needs.get("WATER") is True
    assert res_9.needs.get("FOOD") is True
    assert res_9.needs.get("SHELTER") is False
    water_req = next((r for r in res_9.explicit_requests if r.resource_type == "WATER"), None)
    assert water_req is not None
    assert water_req.quantity == 20
    print("[PASS] Test 9: Explicit quantity preserved without downstream multiplication.")

    # -------------------------------------------------------------
    # TEST 10 — Urgency Extraction
    # -------------------------------------------------------------
    print("\n--- TEST 10: Urgency Extraction ---")
    data_10 = {
        "incident_id": "TEST-10",
        "input_mode": "REPORT",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "description": "Two children are trapped and one person is unconscious.",
    }
    res_10 = agent.assess_incident(data_10, input_mode="REPORT")
    print(f"Result: urgency_keywords={res_10.urgency_keywords}")
    assert "trapped" in res_10.urgency_keywords or any("trapped" in k for k in res_10.urgency_keywords)
    assert "unconscious" in res_10.urgency_keywords or any("unconscious" in k for k in res_10.urgency_keywords)
    print("[PASS] Test 10: Urgency keywords extracted without calculating severity.")

    # -------------------------------------------------------------
    # TEST 11 — Unknown Values
    # -------------------------------------------------------------
    print("\n--- TEST 11: Unknown Values ---")
    data_11 = {
        "incident_id": "TEST-11",
        "input_mode": "SOS",
        "latitude": 28.6139,
        "longitude": 77.2090,
    }
    res_11 = agent.assess_incident(data_11, input_mode="SOS")
    print(f"Result: affected={res_11.people.affected.value}, injured={res_11.people.injured.value}, casualties={res_11.people.casualties.value}")
    assert res_11.people.affected.value is None
    assert res_11.people.injured.value is None
    assert res_11.people.trapped.value is None
    assert res_11.people.missing.value is None
    assert res_11.people.casualties.value is None
    print("[PASS] Test 11: Unknown values strictly preserved as null.")

    # -------------------------------------------------------------
    # TEST 12 — Conflicting Information
    # -------------------------------------------------------------
    print("\n--- TEST 12: Conflicting Information ---")
    data_12 = {
        "incident_id": "TEST-12",
        "input_mode": "REPORT",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "disaster_type": "FLOOD",
        "description": "There is also a fire nearby.",
    }
    res_12 = agent.assess_incident(data_12, input_mode="REPORT")
    print(f"Result: primary disaster={res_12.disaster.type}, source={res_12.disaster.source}, facts={res_12.facts}")
    assert res_12.disaster.type == "FLOOD"
    assert res_12.disaster.source == "USER_FORM"
    assert any("fire" in f.lower() for f in res_12.facts)
    print("[PASS] Test 12: Conflicting information handled correctly (Form primary, description in facts).")

    # -------------------------------------------------------------
    # Pipeline & DB Persistence Verification
    # -------------------------------------------------------------
    print("\n--- PIPELINE INTEGRATION TEST: SOSEvent & Report Persistence ---")
    db = SessionLocal()
    try:
        # 1. Test SOS Creation with Need Agent
        sos_in = SOSCreate(
            reporter_name="Need Agent Test Citizen",
            contact="7977661625",
            latitude=28.6139,
            longitude=77.2090,
            description="Flash flood in sector 4, 3 people trapped upstairs. Need water.",
            food_required=False,
            water_required=True,
        )
        sos_ev, alert, log = sos_service.create_sos(db, sos_in)
        print(f"Created SOSEvent: {sos_ev.incident_id} | assessment_status: {sos_ev.assessment_status}")
        assert sos_ev.assessment_json is not None
        assert sos_ev.assessment_json["disaster"]["type"] == "FLOOD" or sos_ev.disaster_type == "Flood"
        assert sos_ev.assessment_version == "1.0"
        assert sos_ev.assessment_status == "COMPLETED"

        # 2. Test Report Creation with Need Agent
        rep_in = ReportCreate(
            disaster_type="Earthquake",
            description="Tremors felt, 2 injured and need medicine.",
            latitude=28.6139,
            longitude=77.2090,
            people_affected=15,
            people_injured=2,
        )
        rep = report_service.create_report(db, rep_in)
        print(f"Created Report: {rep.id} | assessment_status: {rep.assessment_status}")
        assert rep.assessment_json is not None
        assert rep.assessment_json["people"]["injured"]["value"] == 2
        assert rep.assessment_status == "COMPLETED"
        print("[PASS] Pipeline integration and JSON/JSONB persistence verified.")

    finally:
        db.close()

    print("\n" + "=" * 70)
    print(">>> ALL 12 NEED & ASSESSMENT AGENT TESTS PASSED! <<<")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
