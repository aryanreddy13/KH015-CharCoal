import logging
import base64
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import httpx
from app.config import settings
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_emergency_email(
        recipient: str,
        incident: Dict[str, Any],
        photo_url: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Sends critical emergency alert email to designated emergency service provider via Resend.
        Attaches incident photo if available.
        Returns: (success: bool, status: 'SENT' | 'DEMO' | 'FAILED')
        """
        incident_id = incident.get("incident_id", "SOS-UNKNOWN")
        disaster_type = incident.get("disaster_type", "Flood")
        zone_name = incident.get("zone_name", "Emergency Sector")
        severity = incident.get("severity", 9.5)
        affected = incident.get("people_affected", 0)
        injured = incident.get("injured_people", 0)
        missing = incident.get("missing_people", 0)
        resources = ", ".join(incident.get("required_resources", ["Rescue", "Medical"]))
        lat = incident.get("latitude", 28.6139)
        lng = incident.get("longitude", 77.2090)
        distance = incident.get("distance_km", 4.8)
        eta = incident.get("eta_minutes", 11)
        status = incident.get("provider_status", "NEW")
        created_at = incident.get("created_at", datetime.utcnow().isoformat())

        subject = f"🚨 CRITICAL SOS — {incident_id} — {disaster_type}"
        map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"

        allocations = incident.get("resource_allocations", [])
        allocations_html = ""
        if allocations:
            rows = ""
            for al in allocations:
                st = al.get("status", "ALLOCATED")
                st_color = "#22c55e" if st == "ALLOCATED" else ("#eab308" if st == "PARTIALLY_ALLOCATED" else "#ef4444")
                rows += f"""
                <tr style="border-bottom: 1px solid #1e293b;">
                  <td style="padding: 8px; font-weight: 700; color: #ffffff;">{al.get('resource_type')}</td>
                  <td style="padding: 8px; color: #94a3b8;">{al.get('requested_quantity', 0)} {al.get('unit', '')}</td>
                  <td style="padding: 8px; color: #38bdf8; font-weight: 700;">{al.get('allocated_quantity', 0)} {al.get('unit', '')}</td>
                  <td style="padding: 8px; color: {st_color}; font-weight: 700;">{st}</td>
                </tr>
                """
            allocations_html = f"""
            <div style="margin-top: 16px; background: #070a12; border: 1px solid #334155; border-radius: 8px; padding: 12px;">
              <div style="font-size: 14px; font-weight: 800; color: #f8fafc; margin-bottom: 8px;">📦 AUTOMATED RESOURCE ALLOTMENT BREAKDOWN</div>
              <table style="width: 100%; text-align: left; font-size: 12px; border-collapse: collapse;">
                <thead>
                  <tr style="color: #64748b; border-bottom: 1px solid #334155;">
                    <th style="padding: 6px;">Resource</th>
                    <th style="padding: 6px;">Requested</th>
                    <th style="padding: 6px;">Allocated</th>
                    <th style="padding: 6px;">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows}
                </tbody>
              </table>
            </div>
            """

        # 1. Process Photo Attachment & Embedded Image Data URI
        attachments = []
        photo_html = ""
        if photo_url and str(photo_url).strip():
            img_data = storage_service.get_image_bytes(photo_url)
            if img_data:
                raw_bytes, img_filename = img_data
                b64_content = base64.b64encode(raw_bytes).decode("utf-8")
                img_src = f"data:image/jpeg;base64,{b64_content}"
                if str(photo_url).startswith("http://") or str(photo_url).startswith("https://"):
                    img_src = photo_url

                attachments.append({
                    "filename": f"incident-{incident_id[:8]}.jpg",
                    "content": b64_content,
                })

                photo_html = f"""
                <div style="margin-top: 18px; text-align: center; background: #070a12; border: 2px solid #ef4444; border-radius: 10px; padding: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
                  <div style="font-size: 13px; font-weight: 800; color: #ef4444; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">
                    📷 ON-SCENE INCIDENT EVIDENCE PHOTOGRAPH
                  </div>
                  <img src="{img_src}" alt="Incident Evidence Photo" style="max-width: 100%; max-height: 380px; border-radius: 8px; border: 1px solid #334155; display: block; margin: 0 auto; object-fit: cover;" />
                  <div style="margin-top: 8px; font-size: 11px; color: #94a3b8;">
                    Verified on-scene photographic proof attached to this dispatch.
                  </div>
                </div>
                """

        # HTML Body
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #070a12; color: #f8fafc; padding: 24px; }}
            .container {{ max-width: 620px; margin: 0 auto; background: #0f172a; border-radius: 12px; border: 1px solid #dc2626; padding: 24px; }}
            .badge {{ background: #dc2626; color: #ffffff; padding: 4px 12px; border-radius: 6px; font-weight: 900; display: inline-block; font-size: 12px; }}
            .title {{ font-size: 22px; font-weight: 800; color: #ffffff; margin-top: 12px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0; background: #070a12; padding: 16px; border-radius: 8px; }}
            .field {{ font-size: 13px; color: #94a3b8; }}
            .val {{ font-size: 15px; font-weight: 700; color: #ffffff; }}
            .btn {{ display: inline-block; background: #ef4444; color: #ffffff; text-decoration: none; padding: 12px 20px; border-radius: 8px; font-weight: 800; margin-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <span class="badge">SANJIVANI CRITICAL EMERGENCY ALERT</span>
            <div class="title">Incident: {incident_id} ({disaster_type})</div>
            <p style="color: #cbd5e1; font-size: 14px;">A life-threatening disaster incident requires immediate emergency deployment in <strong>{zone_name}</strong>.</p>
            
            <div class="grid">
              <div><span class="field">Disaster Type:</span><br><span class="val">{disaster_type}</span></div>
              <div><span class="field">Severity Rating:</span><br><span class="val" style="color: #ef4444;">{severity}/10.0</span></div>
              <div><span class="field">People Affected:</span><br><span class="val">{affected}</span></div>
              <div><span class="field">Injured / Missing:</span><br><span class="val">{injured} Injured / {missing} Missing</span></div>
              <div><span class="field">Required Units:</span><br><span class="val">{resources}</span></div>
              <div><span class="field">Estimated Response ETA:</span><br><span class="val" style="color: #38bdf8;">{eta} minutes ({distance} km)</span></div>
              <div><span class="field">Incident Status:</span><br><span class="val">{status}</span></div>
              <div><span class="field">Timestamp:</span><br><span class="val">{created_at}</span></div>
            </div>

            {allocations_html}

            <div>
              <a href="{map_link}" class="btn" style="color: #ffffff;">📍 OPEN GPS LOCATION IN MAPS</a>
            </div>

            {photo_html}

            <p style="color: #64748b; font-size: 12px; margin-top: 24px; border-top: 1px solid #1e293b; padding-top: 12px;">
              Sanjivani - Agentic Disaster Relief & Emergency Resource Coordinator Automated Dispatch Pipeline.
            </p>
          </div>
        </body>
        </html>
        """

        # 2. Check if Resend is enabled & API Key configured
        target_recipient = recipient if recipient and str(recipient).strip() else getattr(settings, "NOTIFICATION_EMAIL", "aryanreddy2006@gmail.com")
        if not settings.ENABLE_RESEND or not settings.RESEND_API_KEY:
            logger.info(
                f"[RESEND_DEMO_TRIGGERED] Emergency Email simulated for {target_recipient} | "
                f"Incident: {incident_id} | Attached photo: {bool(photo_url)}"
            )
            return True, "DEMO"

        # 3. Dispatch via Resend REST API
        try:
            payload = {
                "from": settings.RESEND_FROM_EMAIL or "onboarding@resend.dev",
                "to": [target_recipient],
                "subject": subject,
                "html": html_content,
            }
            if attachments:
                payload["attachments"] = attachments

            headers = {
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=8.0) as client:
                res = client.post("https://api.resend.com/emails", json=payload, headers=headers)
                if res.status_code in (200, 201):
                    logger.info(f"Resend email delivered successfully to {target_recipient} (ID: {incident_id})")
                    return True, "SENT"
                else:
                    logger.warning(f"Resend API returned {res.status_code}: {res.text}")
                    return False, "FAILED"

        except Exception as e:
            logger.error(f"Failed to send emergency email via Resend: {e}")
            return False, "FAILED"

    @staticmethod
    def send_report_email(
        recipient: str,
        report_data: Dict[str, Any],
        photo_url: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Sends citizen manual incident report alert email with evidence photo to disaster response authority.
        """
        report_id = report_data.get("id", "REP-UNKNOWN")
        disaster_type = report_data.get("disaster_type", "Disaster Incident")
        description = report_data.get("description", "No description provided.")
        affected = report_data.get("people_affected", 0)
        injured = report_data.get("injured_people", 0)
        missing = report_data.get("missing_people", 0)
        lat = report_data.get("latitude", 19.0760)
        lng = report_data.get("longitude", 72.8777)
        location_text = report_data.get("location_text") or f"{lat:.4f}°, {lng:.4f}°"
        reporter_name = report_data.get("reporter_name", "Citizen Reporter")
        reporter_phone = report_data.get("reporter_phone", "Not provided")
        created_at = report_data.get("created_at", datetime.utcnow().isoformat())

        subject = f"📋 CITIZEN INCIDENT REPORT — {disaster_type} ({location_text})"
        map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"

        # 1. Process Photo Attachment & Embedded Image Data URI
        attachments = []
        photo_html = ""
        if photo_url and str(photo_url).strip():
            img_data = storage_service.get_image_bytes(photo_url)
            if img_data:
                raw_bytes, img_filename = img_data
                b64_content = base64.b64encode(raw_bytes).decode("utf-8")
                img_src = f"data:image/jpeg;base64,{b64_content}"
                if str(photo_url).startswith("http://") or str(photo_url).startswith("https://"):
                    img_src = photo_url

                attachments.append({
                    "filename": f"evidence-{report_id[:8]}.jpg",
                    "content": b64_content,
                })

                photo_html = f"""
                <div style="margin-top: 18px; text-align: center; background: #070a12; border: 2px solid #38bdf8; border-radius: 10px; padding: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
                  <div style="font-size: 13px; font-weight: 800; color: #38bdf8; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">
                    📷 CITIZEN ON-SCENE EVIDENCE PHOTOGRAPH
                  </div>
                  <img src="{img_src}" alt="Citizen Incident Evidence" style="max-width: 100%; max-height: 380px; border-radius: 8px; border: 1px solid #334155; display: block; margin: 0 auto; object-fit: cover;" />
                  <div style="margin-top: 8px; font-size: 11px; color: #94a3b8;">
                    Verified on-scene photographic proof attached to this dispatch.
                  </div>
                </div>
                """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #070a12; color: #f8fafc; padding: 24px; }}
            .container {{ max-width: 620px; margin: 0 auto; background: #0f172a; border-radius: 12px; border: 1px solid #38bdf8; padding: 24px; }}
            .badge {{ background: #0284c7; color: #ffffff; padding: 4px 12px; border-radius: 6px; font-weight: 900; display: inline-block; font-size: 12px; }}
            .title {{ font-size: 20px; font-weight: 800; color: #ffffff; margin-top: 12px; }}
            .desc {{ background: #070a12; border-left: 3px solid #38bdf8; padding: 12px; margin: 16px 0; font-size: 14px; color: #e2e8f0; line-height: 1.5; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0; background: #070a12; padding: 14px; border-radius: 8px; }}
            .field {{ font-size: 12px; color: #94a3b8; }}
            .val {{ font-size: 14px; font-weight: 700; color: #ffffff; }}
            .btn {{ display: inline-block; background: #0284c7; color: #ffffff; text-decoration: none; padding: 10px 18px; border-radius: 8px; font-weight: 800; margin-top: 12px; font-size: 13px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <span class="badge">CITIZEN INCIDENT REPORT</span>
            <div class="title">{disaster_type} — {location_text}</div>
            
            <div class="desc">
              <strong>Citizen Description:</strong><br>
              "{description}"
            </div>

            <div class="grid">
              <div><span class="field">Reporter Name:</span><br><span class="val">{reporter_name}</span></div>
              <div><span class="field">Contact Phone:</span><br><span class="val">{reporter_phone}</span></div>
              <div><span class="field">People Affected:</span><br><span class="val">{affected}</span></div>
              <div><span class="field">Injured / Missing:</span><br><span class="val">{injured} Injured / {missing} Missing</span></div>
              <div><span class="field">GPS Coordinates:</span><br><span class="val">{lat:.4f}, {lng:.4f}</span></div>
              <div><span class="field">Report Timestamp:</span><br><span class="val">{created_at}</span></div>
            </div>

            <div>
              <a href="{map_link}" class="btn" style="color: #ffffff;">📍 VIEW INCIDENT ON MAP</a>
            </div>

            {photo_html}

            <p style="color: #64748b; font-size: 12px; margin-top: 24px; border-top: 1px solid #1e293b; padding-top: 12px;">
              Sanjivani - Multi-Agency Disaster Operations Portal & Citizen Reporter Pipeline.
            </p>
          </div>
        </body>
        </html>
        """

        target_recipient = recipient if recipient and str(recipient).strip() else getattr(settings, "NOTIFICATION_EMAIL", "aryanreddy2006@gmail.com")
        if not settings.ENABLE_RESEND or not settings.RESEND_API_KEY:
            logger.info(f"[RESEND_DEMO] Citizen Report Email simulated for {target_recipient} | Photo attached: {bool(photo_url)}")
            return True, "DEMO"

        try:
            payload = {
                "from": settings.RESEND_FROM_EMAIL or "onboarding@resend.dev",
                "to": [target_recipient],
                "subject": subject,
                "html": html_content,
            }
            if attachments:
                payload["attachments"] = attachments

            headers = {
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=8.0) as client:
                res = client.post("https://api.resend.com/emails", json=payload, headers=headers)
                if res.status_code in (200, 201):
                    logger.info(f"Citizen report email delivered to {target_recipient}")
                    return True, "SENT"
                else:
                    logger.warning(f"Resend returned {res.status_code}: {res.text}")
                    return False, "FAILED"
        except Exception as e:
            logger.error(f"Error sending citizen report email: {e}")
            return False, "FAILED"

email_service = EmailService()
