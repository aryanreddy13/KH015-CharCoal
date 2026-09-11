"""
Automated Verification Suite for PS20 Priority & Severity Scoring Agent
Tests all required specifications:
1. TEST 1 — Detailed Flood Report (People, Disaster, Urgency components)
2. TEST 2 — Large Affected Population (Logarithmic scaling verification)
3. TEST 3 — Unknown Affected Count (Strict null preservation & fallback tracking)
4. TEST 4 — Unknown Disaster (UNKNOWN disaster mapping)
5. TEST 5 — Multiple Urgency Keywords (Aggregation & Max cap enforcement)
6. TEST 6 — Unknown Keywords (Safe zero-contribution handling)
7. TEST 7 — GPS-only SOS (Stateless fallback verification)
8. TEST 8 — Form Precedence (Canonical assessment trust)
9. TEST 9 — Deterministic Scoring (Consistent output across runs)
10. TEST 10 — Threshold Classification (LOW, MEDIUM, HIGH, CRITICAL levels)
11. TEST 11 — No Resource Allocation (Zero inventory/resource mutation)
12. TEST 12 — End-to-End Pipeline & DB Persistence (SOSEvent & Report storage)
"""

import os
import sys
import math
from pathlib import Path

# Configure UTF-8 stdout for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.agents.need_assessment_agent import need_assessment_agent
from app.agents.priority_severity_agent import priority_severity_agent, PrioritySeverityAgent
from app.schemas.schemas import (
    IncidentAssessment,
    DisasterAssessment,
    PeopleAssessment,
    FactualNumber,
    ExtractionMetadata,
    SOSCreate,
    ReportCreate,
)
from app.services.sos_service import sos_service
from app.services.report_service import report_service
from app.models.models import Resource, ResourceAllocation


def run_all_tests():
    print("=" * 70)
    print("PS20 PRIORITY & SEVERITY SCORING AGENT VERIFICATION SUITE")
    print("=" * 70)

    agent = PrioritySeverityAgent()

    # -------------------------------------------------------------
    # TEST 1 — Detailed Flood Report
    # -------------------------------------------------------------
    print("\n--- TEST 1: Detailed Flood Report ---")
    assessment_1 = IncidentAssessment(
        incident_id="SOS-6235",
        input_mode="REPORT",
        location={"latitude": 28.6139, "longitude": 77.2090},
        disaster=DisasterAssessment(type="FLOOD", source="USER_FORM"),
        people=PeopleAssessment(
            affected=FactualNumber(value=10, source="USER_FORM"),
            injured=FactualNumber(value=2, source="USER_FORM"),
            trapped=FactualNumber(value=5, source="USER_FORM"),
        ),
        urgency_keywords=["trapped", "unconscious"],
        extraction_metadata=ExtractionMetadata(source="USER_FORM"),
    )
    res_1 = agent.score_incident(assessment_1)
    print(f"Result: zone_score={res_1.zone_score}, priority_level={res_1.priority_level}")
    print(f"Components: people={res_1.components.affected_people.score}, disaster={res_1.components.disaster_type.score}, urgency={res_1.components.urgency_keywords.score}")
    
    # log10(11) ≈ 1.04, FLOOD = 4.0, trapped(1.5)+unconscious(2.0) = 3.5 -> 8.54
    assert math.isclose(res_1.components.affected_people.score, 1.04, abs_tol=0.05)
    assert res_1.components.disaster_type.score == 4.0
    assert res_1.components.urgency_keywords.score == 3.5
    assert math.isclose(res_1.zone_score, 8.54, abs_tol=0.05)
    assert res_1.priority_level == "HIGH"
    assert res_1.fallbacks_used == []
    print("[PASS] Test 1: Detailed Flood Report calculated correctly.")

    # -------------------------------------------------------------
    # TEST 2 — Large Affected Population (Logarithmic Scaling)
    # -------------------------------------------------------------
    print("\n--- TEST 2: Large Affected Population (Logarithmic Scaling) ---")
    assessment_2 = IncidentAssessment(
        incident_id="TEST-02",
        input_mode="REPORT",
        location={"latitude": 28.6139, "longitude": 77.2090},
        disaster=DisasterAssessment(type="FLOOD", source="USER_FORM"),
        people=PeopleAssessment(
            affected=FactualNumber(value=1000, source="USER_FORM"),
        ),
        extraction_metadata=ExtractionMetadata(source="USER_FORM"),
    )
    res_2 = agent.score_incident(assessment_2)
    # log10(1001) ≈ 3.00
    print(f"Result: affected=1000 -> people_score={res_2.components.affected_people.score}")
    assert math.isclose(res_2.components.affected_people.score, 3.00, abs_tol=0.05)
    # 1000 people must NOT produce score of 1000 (linear)
    assert res_2.components.affected_people.score < 10.0
    print("[PASS] Test 2: Logarithmic scaling verified (log10(1001) ≈ 3.00).")

    # -------------------------------------------------------------
    # TEST 3 — Unknown Affected Count
    # -------------------------------------------------------------
    print("\n--- TEST 3: Unknown Affected Count ---")
    assessment_3 = IncidentAssessment(
        incident_id="TEST-03",
        input_mode="REPORT",
        location={"latitude": 28.6139, "longitude": 77.2090},
        disaster=DisasterAssessment(type="FIRE", source="USER_FORM"),
        people=PeopleAssessment(
            affected=FactualNumber(value=None, source="UNKNOWN"),
        ),
        extraction_metadata=ExtractionMetadata(source="USER_FORM"),
    )
    res_3 = agent.score_incident(assessment_3)
    print(f"Result: value={res_3.components.affected_people.value}, source={res_3.components.affected_people.source}, fallbacks={res_3.fallbacks_used}")
    # Original assessment remains untouched
    assert assessment_3.people.affected.value is None
    # Output records null value and SYSTEM_FALLBACK source
    assert res_3.components.affected_people.value is None
    assert res_3.components.affected_people.source == "SYSTEM_FALLBACK"
    assert "affected_people" in res_3.fallbacks_used
    # Fallback log10(1+1) ≈ 0.30
    assert math.isclose(res_3.components.affected_people.score, 0.30, abs_tol=0.05)
    print("[PASS] Test 3: Unknown affected count safely handled with fallback source tracking.")

    # -------------------------------------------------------------
    # TEST 4 — Unknown Disaster
    # -------------------------------------------------------------
    print("\n--- TEST 4: Unknown Disaster ---")
    assessment_4 = IncidentAssessment(
        incident_id="TEST-04",
        input_mode="REPORT",
        location={"latitude": 28.6139, "longitude": 77.2090},
        disaster=DisasterAssessment(type=None, source="UNKNOWN"),
        people=PeopleAssessment(
            affected=FactualNumber(value=5, source="USER_FORM"),
        ),
        extraction_metadata=ExtractionMetadata(source="USER_FORM"),
    )
    res_4 = agent.score_incident(assessment_4)
    print(f"Result: disaster_value={res_4.components.disaster_type.value}, score={res_4.components.disaster_type.score}, fallbacks={res_4.fallbacks_used}")
    assert res_4.components.disaster_type.value is None
    assert res_4.components.disaster_type.score == 2.0  # UNKNOWN disaster default
    assert "disaster_type" in res_4.fallbacks_used
    print("[PASS] Test 4: Unknown disaster mapped to default score without hallucination.")

    # -------------------------------------------------------------
    # TEST 5 — Multiple Urgency Keywords & Max Cap
    # -------------------------------------------------------------
    print("\n--- TEST 5: Multiple Urgency Keywords & Max Cap ---")
    assessment_5 = IncidentAssessment(
        incident_id="TEST-05",
        input_mode="REPORT",
        location={"latitude": 28.6139, "longitude": 77.2090},
        disaster=DisasterAssessment(type="EARTHQUAKE", source="USER_FORM"),
        people=PeopleAssessment(
            affected=FactualNumber(value=20, source="USER_FORM"),
        ),
        urgency_keywords=["trapped", "unconscious", "bleeding", "critical", "drowning", "suffocating", "severe bleeding", "children trapped"],
        extraction_metadata=ExtractionMetadata(source="USER_FORM"),
    )
    res_5 = agent.score_incident(assessment_5)
    print(f"Result: matched_keywords={res_5.components.urgency_keywords.matched}, urgency_score={res_5.components.urgency_keywords.score}")
    assert len(res_5.components.urgency_keywords.matched) >= 3
    # Cap enforcement: cannot exceed PRIORITY_MAX_URGENCY_SCORE (10.0)
    assert res_5.components.urgency_keywords.score <= 10.0
    print("[PASS] Test 5: Multiple urgency keywords aggregated and capped at max limit.")

    # -------------------------------------------------------------
    # TEST 6 — Unknown Keywords
    # -------------------------------------------------------------
    print("\n--- TEST 6: Unknown Keywords ---")
    assessment_6 = IncidentAssessment(
        incident_id="TEST-06",
        input_mode="REPORT",
        location={"latitude": 28.6139, "longitude": 77.2090},
        disaster=DisasterAssessment(type="FLOOD", source="USER_FORM"),
        people=PeopleAssessment(
            affected=FactualNumber(value=5, source="USER_FORM"),
        ),
        urgency_keywords=["something_bad_happened_here", "random_unmapped_token"],
        extraction_metadata=ExtractionMetadata(source="USER_FORM"),
    )
    res_6 = agent.score_incident(assessment_6)
    print(f"Result: urgency_score={res_6.components.urgency_keywords.score}, matched={res_6.components.urgency_keywords.matched}")
    assert res_6.components.urgency_keywords.score == 0.0
    assert res_6.components.urgency_keywords.matched == []
    print("[PASS] Test 6: Unknown keywords safely yielded 0.0 contribution without crashing.")

    # -------------------------------------------------------------
    # TEST 7 — GPS-only SOS
    # -------------------------------------------------------------
    print("\n--- TEST 7: GPS-only SOS ---")
    raw_sos = {
        "incident_id": "SOS-9999",
        "input_mode": "SOS",
        "latitude": 19.0760,
        "longitude": 72.8777,
    }
    need_output_sos = need_assessment_agent.assess_incident(raw_sos, input_mode="SOS")
    res_7 = agent.score_incident(need_output_sos)
    print(f"Result: zone_score={res_7.zone_score}, priority_level={res_7.priority_level}, fallbacks={res_7.fallbacks_used}")
    assert "affected_people" in res_7.fallbacks_used
    assert "disaster_type" in res_7.fallbacks_used
    assert res_7.components.urgency_keywords.score == 0.0
    assert res_7.priority_level == "LOW"
    print("[PASS] Test 7: GPS-only SOS handled purely via baseline mathematical model.")

    # -------------------------------------------------------------
    # TEST 8 — Form Precedence Trust
    # -------------------------------------------------------------
    print("\n--- TEST 8: Form Precedence Trust ---")
    assessment_8 = IncidentAssessment(
        incident_id="TEST-08",
        input_mode="REPORT",
        location={"latitude": 28.6139, "longitude": 77.2090},
        disaster=DisasterAssessment(type="FLOOD", source="USER_FORM"),
        people=PeopleAssessment(
            affected=FactualNumber(value=20, source="USER_FORM"),
        ),
        facts=["User text says maybe 100 people around"],
        extraction_metadata=ExtractionMetadata(source="USER_FORM"),
    )
    res_8 = agent.score_incident(assessment_8)
    # Priority Agent uses value=20 directly without reinterpreting facts
    assert res_8.components.affected_people.value == 20
    assert math.isclose(res_8.components.affected_people.score, math.log10(21), abs_tol=0.01)
    print("[PASS] Test 8: Form precedence trusted from canonical assessment.")

    # -------------------------------------------------------------
    # TEST 9 — Deterministic Scoring
    # -------------------------------------------------------------
    print("\n--- TEST 9: Deterministic Scoring ---")
    runs = [agent.score_incident(assessment_1) for _ in range(5)]
    scores = [r.zone_score for r in runs]
    levels = [r.priority_level for r in runs]
    print(f"5 Identical Runs: scores={scores}, levels={levels}")
    assert all(s == scores[0] for s in scores)
    assert all(l == levels[0] for l in levels)
    print("[PASS] Test 9: Strict deterministic scoring verified across repeated runs.")

    # -------------------------------------------------------------
    # TEST 10 — Threshold Classification
    # -------------------------------------------------------------
    print("\n--- TEST 10: Threshold Classification ---")
    # Low score: Road accident (2.5) + 1 affected (0.3) = 2.8 -> LOW
    low_ass = IncidentAssessment(
        incident_id="T-LOW",
        input_mode="REPORT",
        location={"latitude": 0, "longitude": 0},
        disaster=DisasterAssessment(type="ROAD_ACCIDENT", source="USER_FORM"),
        people=PeopleAssessment(affected=FactualNumber(value=1, source="USER_FORM")),
        extraction_metadata=ExtractionMetadata(source="USER_FORM"),
    )
    res_low = agent.score_incident(low_ass)
    print(f"Low check: score={res_low.zone_score}, level={res_low.priority_level}")
    assert res_low.priority_level == "LOW"

    # Critical score: Earthquake (5.0) + 100 affected (2.0) + trapped(1.5)+unconscious(2.0) = 10.5 -> CRITICAL
    crit_ass = IncidentAssessment(
        incident_id="T-CRIT",
        input_mode="REPORT",
        location={"latitude": 0, "longitude": 0},
        disaster=DisasterAssessment(type="EARTHQUAKE", source="USER_FORM"),
        people=PeopleAssessment(affected=FactualNumber(value=100, source="USER_FORM")),
        urgency_keywords=["trapped", "unconscious", "critical"],
        extraction_metadata=ExtractionMetadata(source="USER_FORM"),
    )
    res_crit = agent.score_incident(crit_ass)
    print(f"Critical check: score={res_crit.zone_score}, level={res_crit.priority_level}")
    assert res_crit.priority_level == "CRITICAL"
    print("[PASS] Test 10: Threshold classification boundaries verified.")

    # -------------------------------------------------------------
    # TEST 11 — No Resource Allocation / DB Mutation
    # -------------------------------------------------------------
    print("\n--- TEST 11: No Resource Allocation / DB Mutation ---")
    db = SessionLocal()
    try:
        initial_res_count = db.query(Resource).count()
        initial_alloc_count = db.query(ResourceAllocation).count()

        # Score a high-urgency incident
        agent.score_incident(crit_ass)

        final_res_count = db.query(Resource).count()
        final_alloc_count = db.query(ResourceAllocation).count()

        assert initial_res_count == final_res_count
        assert initial_alloc_count == final_alloc_count
        print(f"DB check: Resource rows={final_res_count}, Allocation rows={final_alloc_count} (Unchanged)")
        print("[PASS] Test 11: Priority Agent does not mutate inventory or resource allocations.")
    finally:
        db.close()

    # -------------------------------------------------------------
    # TEST 12 — End-to-End Pipeline & DB Persistence
    # -------------------------------------------------------------
    print("\n--- TEST 12: End-to-End Pipeline & DB Persistence ---")
    db = SessionLocal()
    try:
        # Test SOS Creation with Priority Agent
        sos_in = SOSCreate(
            reporter_name="Priority Test Citizen",
            contact="7977661625",
            latitude=28.6139,
            longitude=77.2090,
            description="Major building collapse, 10 people trapped upstairs. Immediate rescue needed!",
            disaster_type="Building_Collapse",
            people_affected=10,
        )
        sos_ev, alert, log = sos_service.create_sos(db, sos_in)
        print(f"Created SOSEvent: {sos_ev.incident_id} | priority_score={sos_ev.priority_score} | priority_level={sos_ev.priority_level}")
        assert sos_ev.priority_assessment_json is not None
        assert sos_ev.priority_score is not None
        assert sos_ev.priority_level in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        assert sos_ev.priority_scoring_version == "1.0"

        # Test Report Creation with Priority Agent
        rep_in = ReportCreate(
            disaster_type="Flood",
            description="River overflowed, 8 people trapped in home.",
            latitude=28.6139,
            longitude=77.2090,
            people_affected=8,
        )
        rep = report_service.create_report(db, rep_in)
        print(f"Created Report: {rep.id} | priority_score={rep.priority_score} | priority_level={rep.priority_level}")
        assert rep.priority_assessment_json is not None
        assert rep.priority_score is not None
        assert rep.priority_level in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        print("[PASS] Test 12: End-to-End SOSEvent & Report priority persistence verified.")
    finally:
        db.close()

    print("\n" + "=" * 70)
    print(">>> ALL 12 PRIORITY & SEVERITY AGENT TESTS PASSED! <<<")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
