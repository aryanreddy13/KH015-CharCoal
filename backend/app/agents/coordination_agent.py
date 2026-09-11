"""
Coordination Agent - Multi-Agency Incident Routing & De-duplication Layer
"""

import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import Agency

logger = logging.getLogger(__name__)

class CoordinationAgent:
    def __init__(self):
        self.channel = "inter-agency-mesh"

    def determine_relevant_providers(
        self,
        db: Session,
        disaster_type: str,
        description: str,
        severity: float,
        affected_people: int = 1,
        injured_people: int = 0,
        missing_people: int = 0,
        required_resources: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Determines which emergency provider agencies should respond, assigning priority and required actions.
        Rules:
          - Flood + trapped/casualties: Fire & Rescue (CRITICAL), Medical (CRITICAL), Police (SUPPORT), NGO (RELIEF)
          - Medical emergency / high injuries: Medical (CRITICAL), Police (SUPPORT), Fire & Rescue (SUPPORT)
          - Food / Water / Shelter shortage: NGO (CRITICAL), Government (SUPPORT)
          - Security / Collapse / Fire: Police (CRITICAL), Fire & Rescue (CRITICAL), Medical (SUPPORT)
        """
        if required_resources is None:
            required_resources = []

        desc_lower = (description or "").lower()
        type_lower = (disaster_type or "").lower()
        req_lower = [r.lower() for r in required_resources]

        # Fetch all available agencies
        all_agencies = db.query(Agency).filter(Agency.status == "ACTIVE").all()
        agency_map = {a.type: a for a in all_agencies}

        routes = []

        # Helper to append routing decision
        def add_route(agency_type: str, priority: str, reason: str, res_needed: List[str]):
            agency = agency_map.get(agency_type)
            if agency:
                routes.append({
                    "agency_id": agency.id,
                    "agency_name": agency.name,
                    "agency_type": agency.type,
                    "contact_number": agency.contact_number,
                    "email": agency.email,
                    "priority": priority,  # CRITICAL, HIGH, SUPPORT, RELIEF
                    "reason": reason,
                    "required_resources": res_needed,
                })

        # Rule 1: Flood or Trapped Water Rescue
        if "flood" in type_lower or "water" in desc_lower or "trapped" in desc_lower:
            add_route("FIRE_RESCUE", "CRITICAL", "Flood evacuation, boats and water rescue operations", ["Rescue"])
            if injured_people > 0 or severity >= 8.0:
                add_route("MEDICAL", "CRITICAL", "Triage and trauma care for flood victims", ["Medical", "Medicine"])
            add_route("POLICE", "SUPPORT", "Perimeter security, road closure, crowd evacuation corridor", ["Rescue"])
            if affected_people >= 50 or "food" in req_lower or "water" in req_lower:
                add_route("NGO", "RELIEF", "Emergency food and potable water distribution", ["Food", "Water"])

        # Rule 2: Earthquake, Collapse, Fire
        elif "earthquake" in type_lower or "collapse" in desc_lower or "fire" in type_lower:
            add_route("FIRE_RESCUE", "CRITICAL", "Search & rescue, debris extrication, fire suppression", ["Rescue"])
            add_route("MEDICAL", "CRITICAL", "Field trauma hospital and ICU ambulance dispatch", ["Medical"])
            add_route("POLICE", "SUPPORT", "Cordon hazardous collapse perimeter and control traffic", ["Rescue"])
            if affected_people >= 20 or "shelter" in req_lower:
                add_route("GOVERNMENT", "SUPPORT", "Temporary shelter pods and emergency rehabilitation", ["Shelter"])

        # Rule 3: Direct Medical Emergency
        elif "medical" in req_lower or injured_people > 0:
            add_route("MEDICAL", "CRITICAL", "Urgent medical attention and emergency paramedic dispatch", ["Medical", "Medicine"])
            add_route("POLICE", "SUPPORT", "Green corridor traffic clearance for ambulances", ["Rescue"])
            add_route("FIRE_RESCUE", "SUPPORT", "Physical extrication if required", ["Rescue"])

        # Rule 4: Supply Deficit (Food, Water, Shelter)
        elif "food" in req_lower or "water" in req_lower or "shelter" in req_lower:
            add_route("NGO", "CRITICAL", "Direct relief supply deployment", ["Food", "Water", "Shelter"])
            add_route("GOVERNMENT", "SUPPORT", "Logistics backbone and regional distribution clearance", ["Shelter"])

        # Default fallback
        else:
            add_route("FIRE_RESCUE", "CRITICAL" if severity >= 7.0 else "SUPPORT", "General disaster response mobilization", ["Rescue"])
            if injured_people > 0 or severity >= 6.0:
                add_route("MEDICAL", "CRITICAL" if injured_people > 5 else "SUPPORT", "Medical readiness and emergency triage", ["Medical"])
            add_route("POLICE", "SUPPORT", "Law enforcement and sector security", ["Rescue"])
            add_route("NGO", "RELIEF", "Relief and basic necessities support", ["Food", "Water"])

        logger.info(f"Coordination Agent routed incident ({disaster_type}, sev={severity}) to {len(routes)} agencies: {[r['agency_name'] for r in routes]}")
        return routes

coordination_agent = CoordinationAgent()
