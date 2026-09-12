import httpx
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import settings
from app.services.email_service import email_service

print("Testing direct Resend email...")
print("RESEND_API_KEY:", settings.RESEND_API_KEY[:8] + "..." if settings.RESEND_API_KEY else "None")
print("RESEND_FROM_EMAIL:", settings.RESEND_FROM_EMAIL)
print("NOTIFICATION_EMAIL:", settings.NOTIFICATION_EMAIL)

# 1. Test raw Resend API
headers = {
    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
    "Content-Type": "application/json",
}
payload = {
    "from": "onboarding@resend.dev",
    "to": [settings.NOTIFICATION_EMAIL],
    "subject": "🚨 SANJIVANI RESEND VERIFICATION - Photo Evidence Test",
    "html": "<h2>SANJIVANI EMERGENCY ALERT</h2><p>This is a verification test to confirm delivery to your inbox with evidence photo.</p><img src='https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=600&q=80' width='400' style='border-radius:8px;' />",
}

with httpx.Client(timeout=10.0) as client:
    res = client.post("https://api.resend.com/emails", json=payload, headers=headers)
    print("\n--- RAW RESEND API RESULT ---")
    print("HTTP Status Code:", res.status_code)
    print("Response JSON:", res.text)

# 2. Test full email_service.send_report_email
print("\n--- FULL EMAIL SERVICE TEST ---")
sample_report = {
    "id": "REP-VERIFY-01",
    "disaster_type": "Flood",
    "description": "Verification dispatch with on-scene evidence photograph.",
    "people_affected": 25,
    "injured_people": 3,
    "missing_people": 1,
    "latitude": 19.0178,
    "longitude": 72.8478,
    "location_text": "Hindmata, Dadar, Mumbai",
    "reporter_name": "Emergency Operations Command",
    "reporter_phone": "+91-98200-11223",
}
photo_url = "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80"
success, status = email_service.send_report_email(
    recipient=settings.NOTIFICATION_EMAIL,
    report_data=sample_report,
    photo_url=photo_url,
)
print(f"send_report_email result: success={success}, status={status}")
