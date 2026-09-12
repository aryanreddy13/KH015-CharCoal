import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_endpoint(name, method, path, expected_status=[200, 201], payload=None):
    if isinstance(expected_status, int):
        expected_status = [expected_status]
    url = f"{BASE_URL}{path}"
    start_time = time.time()
    try:
        if method == "GET":
            res = requests.get(url, timeout=10)
        elif method == "POST":
            res = requests.post(url, json=payload or {}, timeout=15)
        elif method == "PUT":
            res = requests.put(url, json=payload or {}, timeout=10)
        
        duration_ms = int((time.time() - start_time) * 1000)
        passed = res.status_code in expected_status
        status_symbol = "[PASS]" if passed else f"[FAIL (Status {res.status_code})]"
        
        print(f"{status_symbol:<14} {method:<4} {path:<40} | {duration_ms:>4}ms")
        if not passed:
            print(f"       Response text: {res.text[:200]}")
            return False, None
        
        try:
            data = res.json()
            return True, data
        except Exception:
            return True, res.text
            
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        print(f"[ERROR]        {method:<4} {path:<40} | {duration_ms:>4}ms | Error: {e}")
        return False, None

def run_all_tests():
    print_header("SANJIVANI DISASTER PLATFORM - END-TO-END API TEST SUITE")
    
    results = []

    # 1. Health & Core
    print("\n--- 1. Health & Metrics Core ---")
    p, data = test_endpoint("Health Check", "GET", "/health", 200)
    results.append(("GET /health", p))
    
    p, data = test_endpoint("Dashboard Summary", "GET", "/summary", 200)
    results.append(("GET /summary", p))

    # 2. Operational Zones
    print("\n--- 2. Geospatial Operational Zones ---")
    p, zones = test_endpoint("List Zones", "GET", "/zones", 200)
    results.append(("GET /zones", p))
    zone_id = None
    if p and isinstance(zones, list) and len(zones) > 0:
        zone_id = zones[0]["id"]
        print(f"       Found {len(zones)} operational sectors. Sample: {zones[0]['name']}")
        p, _ = test_endpoint(f"Get Zone Details", "GET", f"/zones/{zone_id}", 200)
        results.append(("GET /zones/{id}", p))

    # 3. Resources & Inventory
    print("\n--- 3. Multi-Agency Resource Inventory ---")
    p, resources = test_endpoint("List Resources", "GET", "/resources", 200)
    results.append(("GET /resources", p))
    if p and isinstance(resources, list) and len(resources) > 0:
        print(f"       Found {len(resources)} fleet/inventory items. Sample: {resources[0]['name']} ({resources[0]['status']})")
        res_id = resources[0]["id"]
        p, _ = test_endpoint("Get Resource Details", "GET", f"/resources/{res_id}", 200)
        results.append(("GET /resources/{id}", p))

    # 4. Allocations & Active Convoys
    print("\n--- 4. Active Allocations & Convoys ---")
    p, allocs = test_endpoint("List Allocations", "GET", "/allocations", 200)
    results.append(("GET /allocations", p))
    if p and isinstance(allocs, list):
        print(f"       Found {len(allocs)} active resource allocations/convoys.")

    # 5. Agencies & Providers
    print("\n--- 5. Responder Agencies & Providers ---")
    p, agencies = test_endpoint("List Agencies", "GET", "/agencies", 200)
    results.append(("GET /agencies", p))
    if p and isinstance(agencies, list):
        print(f"       Found {len(agencies)} registered emergency agencies.")

    # 6. Needs Manifest
    print("\n--- 6. Sector Resource Needs Manifest ---")
    p, needs = test_endpoint("List Needs", "GET", "/needs", 200)
    results.append(("GET /needs", p))

    # 7. Citizen Incident Reports
    print("\n--- 7. Citizen Incident Reporting ---")
    p, reports = test_endpoint("List Reports", "GET", "/reports", 200)
    results.append(("GET /reports", p))
    
    new_report_payload = {
        "disaster_type": "Flood",
        "description": "Rising water level near residential block. 15 people trapped on terrace.",
        "people_affected": 15,
        "injured_people": 2,
        "missing_people": 0,
        "latitude": 19.0760,
        "longitude": 72.8777,
        "location_text": "Kurla West, Mumbai",
        "reporter_name": "E2E Test User",
        "reporter_phone": "+91-9876543210",
        "required_resources": ["Rescue", "Medical"]
    }
    p, rep_data = test_endpoint("Create Incident Report", "POST", "/reports", [200, 201], new_report_payload)
    results.append(("POST /reports", p))

    # 8. Alerts & Broadcasting
    print("\n--- 8. Alerting & Notifications ---")
    p, alerts = test_endpoint("List Alerts", "GET", "/alerts", 200)
    results.append(("GET /alerts", p))
    
    new_alert_payload = {
        "title": "E2E Test Advisory Alert",
        "message": "High rainfall alert in western coastal sectors.",
        "alert_level": "WARNING",
        "zone_id": zone_id
    }
    p, alert_data = test_endpoint("Broadcast Alert", "POST", "/alerts", [200, 201], new_alert_payload)
    results.append(("POST /alerts", p))

    # 9. System Audit Trail
    print("\n--- 9. System Audit Trail ---")
    p, logs = test_endpoint("List Audit Logs", "GET", "/audit-logs?limit=10", 200)
    results.append(("GET /audit-logs", p))

    # 10. Emergency Services & Roadmap
    print("\n--- 10. Emergency Roadmap & Proximity ---")
    p, services = test_endpoint("Nearest Emergency Services", "GET", "/emergency-services/nearby?latitude=19.0760&longitude=72.8777", 200)
    results.append(("GET /emergency-services/nearby", p))

    # 11. SOS Emergency Beacon
    print("\n--- 11. Citizen SOS Emergency Beacon ---")
    sos_payload = {
        "reporter_name": "SOS Beacon Test",
        "contact": "+91-9988776655",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "accuracy": 5.0,
        "description": "E2E Emergency SOS Verification Beacon",
        "disaster_type": "Flood",
        "severity": 9.0,
        "people_affected": 20,
        "injured_people": 3,
        "missing_people": 0,
        "required_resources": ["Rescue", "Medical"]
    }
    p, sos_data = test_endpoint("Trigger SOS Emergency Beacon", "POST", "/sos", [200, 201], sos_payload)
    results.append(("POST /sos", p))

    # 12. Simulation Harness
    print("\n--- 12. Agentic Simulation Engine ---")
    p, sim_start = test_endpoint("Trigger Start Simulation", "POST", "/simulation/start", 200)
    results.append(("POST /simulation/start", p))

    p, sim_emerg = test_endpoint("Trigger Pan-India Emergency", "POST", "/simulation/emergency", 200)
    results.append(("POST /simulation/emergency", p))

    p, sim_block = test_endpoint("Trigger Roadblock Simulation", "POST", "/simulation/road-block", 200)
    results.append(("POST /simulation/road-block", p))

    # Summary
    print_header("FINAL TEST RESULTS SUMMARY")
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n  Total Endpoints Tested : {total_count}")
    print(f"  Passed                : {passed_count}")
    print(f"  Failed                : {total_count - passed_count}")
    print(f"  Success Rate          : {(passed_count/total_count)*100:.1f}%\n")
    
    for name, passed in results:
        status_str = "[PASS]" if passed else "[FAIL]"
        print(f"  {status_str:<10} | {name}")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
