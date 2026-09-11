import logging
from typing import Dict, Any, Tuple
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

PAGERDUTY_EVENTS_V2_URL = "https://events.pagerduty.com/v2/enqueue"

class PagerDutyService:
    @staticmethod
    def trigger_pagerduty_incident(
        incident: Dict[str, Any],
        provider: Dict[str, Any],
        affected_count: int = 1,
        injured_count: int = 0,
        missing_count: int = 0,
        eta: int = 11,
    ) -> Tuple[bool, str]:
        """
        Triggers emergency escalation incident on PagerDuty via Events API v2.
        Embeds short automated emergency call/SMS message payload.
        Returns: (success: bool, status: 'SENT' | 'DEMO' | 'FAILED')
        """
        incident_id = incident.get("incident_id", "SOS-UNKNOWN")
        disaster_type = incident.get("disaster_type", "Disaster")
        zone_name = incident.get("zone_name", "Emergency Sector")
        severity = incident.get("severity", 9.5)
        provider_name = provider.get("name", "Emergency Response Team")
        lat = incident.get("latitude", 28.6139)
        lng = incident.get("longitude", 77.2090)
        distance_km = incident.get("distance_km", 4.8)
        resources_str = ", ".join(incident.get("required_resources", ["Rescue", "Medical"]))

        automated_message = (
            f"PS20 CRITICAL SOS. {disaster_type} emergency at {zone_name}. "
            f"{affected_count} people affected, {injured_count} injured, {missing_count} missing. "
            f"{provider_name} response is required. Estimated arrival {eta} minutes."
        )

        # 1. Check if PagerDuty is enabled & Routing key configured
        if not settings.ENABLE_PAGERDUTY or not settings.PAGERDUTY_ROUTING_KEY:
            logger.info(
                f"[PAGERDUTY_DEMO_TRIGGERED] Escalation simulated for {provider_name} | "
                f"Incident: {incident_id} | Automated Voice: '{automated_message}'"
            )
            return True, "DEMO"

        # 2. Build Events API v2 payload
        payload = {
            "routing_key": settings.PAGERDUTY_ROUTING_KEY,
            "event_action": "trigger",
            "dedup_key": f"ps20-incident-{incident_id}",
            "payload": {
                "summary": f"🚨 PS20 CRITICAL SOS — {zone_name} — {disaster_type}",
                "severity": "critical",
                "source": "PS20 Emergency Dispatch Coordinator",
                "component": provider_name,
                "group": "Disaster Response Operations",
                "custom_details": {
                    "automated_call_message": automated_message,
                    "incident_id": incident_id,
                    "disaster_type": disaster_type,
                    "zone": zone_name,
                    "severity_score": severity,
                    "people_affected": affected_count,
                    "injured": injured_count,
                    "missing": missing_count,
                    "required_resources": resources_str,
                    "location_gps": f"{lat:.4f}, {lng:.4f}",
                    "distance_km": distance_km,
                    "eta_minutes": eta,
                },
            },
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(PAGERDUTY_EVENTS_V2_URL, json=payload)
                if res.status_code in (200, 202):
                    logger.info(f"PagerDuty incident triggered for {provider_name} (ID: {incident_id})")
                    return True, "SENT"
                else:
                    logger.warning(f"PagerDuty API returned {res.status_code}: {res.text}")
                    return False, "FAILED"
        except Exception as e:
            logger.error(f"Failed to trigger PagerDuty incident: {e}")
            return False, "FAILED"

pagerduty_service = PagerDutyService()
