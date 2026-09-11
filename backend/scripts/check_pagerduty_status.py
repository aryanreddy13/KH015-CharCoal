import os
import sys
import httpx

# Add backend directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import settings

def check_status():
    print("=" * 65)
    print("PS20 - PAGERDUTY LIVE API CONFIGURATION CHECK")
    print("=" * 65)
    
    api_key = settings.PAGERDUTY_API_KEY
    routing_key = settings.PAGERDUTY_ROUTING_KEY
    print(f"Routing Key: {routing_key}")
    print(f"API Key:     {api_key[:6]}...{api_key[-4:] if len(api_key) > 10 else ''}\n")

    headers = {
        "Authorization": f"Token token={api_key}",
        "Accept": "application/vnd.pagerduty+json;version=2",
        "Content-Type": "application/json",
    }
    client = httpx.Client(timeout=8.0)

    # 1. Users & Phone Verification
    print("[1] Responder Users & Contact Verification Status:")
    try:
        res = client.get("https://api.pagerduty.com/users", headers=headers)
        if res.status_code == 200:
            users = res.json().get("users", [])
            for u in users:
                uid = u.get("id")
                uname = u.get("name")
                email = u.get("email")
                
                cm_res = client.get(f"https://api.pagerduty.com/users/{uid}/contact_methods", headers=headers)
                cms = cm_res.json().get("contact_methods", []) if cm_res.status_code == 200 else []
                
                nr_res = client.get(f"https://api.pagerduty.com/users/{uid}/notification_rules", headers=headers)
                nrs = nr_res.json().get("notification_rules", []) if nr_res.status_code == 200 else []
                
                print(f"  - User: {uname} ({email}) | ID: {uid}")
                for cm in cms:
                    cm_type = cm.get("type")
                    addr = cm.get("address")
                    cc = cm.get("country_code", "")
                    enabled = cm.get("enabled", False)
                    cc_str = f"+{cc} " if cc else ""
                    status_str = "[VERIFIED / ACTIVE]" if enabled else "[UNVERIFIED / BLOCKED]"
                    print(f"      * {cm_type:20} -> {cc_str}{addr:15} {status_str}")
        else:
            print(f"  Error fetching users ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"  Exception checking users: {e}")

    # 2. Check Service & Escalation Policy
    print("\n[2] Service & Escalation Policy Assignment:")
    try:
        res = client.get("https://api.pagerduty.com/services?include[]=integrations", headers=headers)
        if res.status_code == 200:
            svcs = res.json().get("services", [])
            for s in svcs:
                sname = s.get("name")
                ep = s.get("escalation_policy", {}).get("summary", "None")
                integs = s.get("integrations", [])
                integ_keys = [i.get("integration_key") for i in integs]
                matches = routing_key in integ_keys
                print(f"  - Service: '{sname}' | Escalation Policy: '{ep}'")
                print(f"    Integration Key Match ({routing_key}): {'YES (ACTIVE)' if matches else 'NO'}")
        else:
            print(f"  Error fetching services: {res.status_code}")
    except Exception as e:
        print(f"  Exception checking services: {e}")

    # 3. Check Recent Incident Triggers
    print("\n[3] Latest Triggered Incidents:")
    try:
        res = client.get("https://api.pagerduty.com/incidents?limit=3&sort_by=created_at:desc", headers=headers)
        if res.status_code == 200:
            incs = res.json().get("incidents", [])
            for inc in incs:
                inum = inc.get("incident_number")
                title = inc.get("title", "").encode("ascii", "ignore").decode("ascii")
                status = inc.get("status")
                urgency = inc.get("urgency")
                svc = inc.get("service", {}).get("summary")
                created = inc.get("created_at")
                assignees = [a.get("assignee", {}).get("summary") for a in inc.get("assignments", [])]
                print(f"  - Incident #{inum} [{status.upper()}] (Urgency: {urgency}) | Service: {svc}")
                print(f"    Title: {title}")
                print(f"    Assigned Responders: {', '.join(assignees) if assignees else 'None'}")
                print(f"    Created: {created}\n")
    except Exception as e:
        print(f"  Exception checking incidents: {e}")

    print("=" * 65)

if __name__ == "__main__":
    check_status()
