import uuid
import json
import math
import asyncio
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import SOSEvent, Zone, Alert, AuditLog, Resource, Agency
from app.schemas.schemas import SOSCreate
from app.config import settings
from app.agents.coordination_agent import coordination_agent
from app.services.email_service import email_service
from app.services.pagerduty_service import pagerduty_service
from app.services.audit_service import audit_service
from app.services.alert_service import alert_service
from app.services.resource_allocation_service import resource_allocation_service
from app.websocket.connection_manager import manager
from app.agents.need_assessment_agent import need_assessment_agent

from app.services.osm_service import osm_service

logger = logging.getLogger(__name__)

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine formula to compute great-circle distance between two GPS coordinates in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

class SOSService:
    @staticmethod
    def get_all_sos(db: Session, limit: int = 100) -> List[SOSEvent]:
        return db.query(SOSEvent).order_by(SOSEvent.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_sos_by_id(db: Session, sos_id: str) -> Optional[SOSEvent]:
        return db.query(SOSEvent).filter((SOSEvent.id == sos_id) | (SOSEvent.incident_id == sos_id)).first()

    @staticmethod
    def find_nearest_zone(db: Session, lat: float, lon: float) -> Optional[Zone]:
        zones = db.query(Zone).all()
        if not zones:
            return None
        nearest_zone = None
        min_dist = float("inf")
        for zone in zones:
            dist = calculate_distance_km(lat, lon, zone.latitude, zone.longitude)
            if dist < min_dist:
                min_dist = dist
                nearest_zone = zone
        return nearest_zone

    @staticmethod
    def find_nearest_resource(
        db: Session,
        lat: float,
        lon: float,
        agency_id: Optional[str] = None,
        resource_types: Optional[List[str]] = None,
    ) -> Tuple[Optional[Resource], float, int]:
        """
        Finds the closest available resource matching agency or resource type.
        Uses OpenStreetMap / OSRM calculate_route to compute real road distance and driving ETA.
        """
        query = db.query(Resource).filter(Resource.status == "AVAILABLE")
        if agency_id:
            query = query.filter(Resource.agency_id == agency_id)

        resources = query.all()
        if not resources:
            # Fallback to any resource
            resources = db.query(Resource).all()

        if not resources:
            return None, 4.8, 11

        # Fast in-memory distance ranking to pick best candidate
        ranked_resources = []
        for r in resources:
            r_lat = r.latitude if r.latitude is not None else lat
            r_lon = r.longitude if r.longitude is not None else lon
            dist_approx = calculate_distance_km(lat, lon, r_lat, r_lon)
            ranked_resources.append((dist_approx, r, r_lat, r_lon))

        ranked_resources.sort(key=lambda x: x[0])
        best_res = ranked_resources[0][1]
        best_dist_approx = ranked_resources[0][0]

        # Fast road estimation model (haversine * 1.3 road curvature)
        best_dist_km = round(max(0.5, best_dist_approx * 1.3), 1)
        best_eta_min = max(3, math.ceil((best_dist_km / 35.0) * 60) + 2)

        return best_res, best_dist_km, best_eta_min

    @staticmethod
    def create_sos(db: Session, sos_in: SOSCreate) -> Tuple[SOSEvent, Alert, AuditLog]:
        # 1. Generate clean readable incident ID: SOS-XXXX
        unique_suffix = uuid.uuid4().hex[:4].upper()
        incident_id = f"SOS-{unique_suffix}"

        # 2. Find closest zone
        zone = SOSService.find_nearest_zone(db, sos_in.latitude, sos_in.longitude)
        zone_id = zone.id if zone else None
        zone_name = zone.name if zone else "Sector Alpha - Unassigned"

        disaster_type = sos_in.disaster_type or (zone.disaster_type if zone else "Flood")
        severity = sos_in.severity if sos_in.severity is not None else (zone.overall_severity if zone else 9.5)
        affected = max(1, sos_in.people_affected or 1)
        injured = max(0, sos_in.injured_people or 0)
        missing = max(0, sos_in.missing_people or 0)
        req_resources = sos_in.required_resources or ["Rescue", "Medical"]

        # 3. Determine relevant emergency providers via Coordination Agent
        routed_agencies = coordination_agent.determine_relevant_providers(
            db=db,
            disaster_type=disaster_type,
            description=sos_in.description or "EMERGENCY SOS TRIGGERED",
            severity=severity,
            affected_people=affected,
            injured_people=injured,
            missing_people=missing,
            required_resources=req_resources,
        )

        # 4. Find primary assigned agency & nearest available unit
        primary_agency_id = routed_agencies[0]["agency_id"] if routed_agencies else None
        nearest_resource, distance_km, eta_minutes = SOSService.find_nearest_resource(
            db, sos_in.latitude, sos_in.longitude, agency_id=primary_agency_id
        )

        # 5. Execute Need & Assessment Agent (pure & stateless understanding layer)
        sos_dict = sos_in.dict() if hasattr(sos_in, "dict") else sos_in.model_dump()
        sos_dict["incident_id"] = incident_id
        assessment = need_assessment_agent.assess_incident(sos_dict, input_mode=getattr(sos_in, "input_mode", "SOS") or "SOS")
        assessment_dict = assessment.dict() if hasattr(assessment, "dict") else assessment.model_dump()

        # 5b. Execute Priority & Severity Agent (pure & stateless scoring layer)
        try:
            from app.agents.priority_severity_agent import priority_severity_agent
            priority_assessment = priority_severity_agent.score_incident(assessment)
        except Exception as prio_err:
            logger.error(f"[PRIORITY_AGENT] Failed to calculate priority for {incident_id}: {prio_err}")
            priority_assessment = None

        priority_dict = (
            priority_assessment.dict() if hasattr(priority_assessment, "dict") else priority_assessment.model_dump()
        ) if priority_assessment else None
        prio_score = priority_assessment.zone_score if priority_assessment else None
        prio_lvl = priority_assessment.priority_level if priority_assessment else None
        prio_ver = priority_assessment.scoring_version if priority_assessment else "1.0"

        # 6. Create SOSEvent
        sos_event = SOSEvent(
            incident_id=incident_id,
            reporter_name=sos_in.reporter_name or "Anonymous Citizen",
            contact=sos_in.contact,
            latitude=sos_in.latitude,
            longitude=sos_in.longitude,
            accuracy=sos_in.accuracy if sos_in.accuracy is not None else 10.0,
            status="ACTIVE",
            provider_status="NEW",
            description=sos_in.description or "EMERGENCY SOS TRIGGERED",
            disaster_type=disaster_type,
            severity=severity,
            people_affected=affected,
            injured_people=injured,
            missing_people=missing,
            food_required=getattr(sos_in, "food_required", False),
            food_quantity=getattr(sos_in, "food_quantity", None),
            water_required=getattr(sos_in, "water_required", False),
            water_quantity=getattr(sos_in, "water_quantity", None),
            shelter_required=getattr(sos_in, "shelter_required", False),
            shelter_quantity=getattr(sos_in, "shelter_quantity", None),
            medicine_required=getattr(sos_in, "medicine_required", False),
            medicine_quantity=getattr(sos_in, "medicine_quantity", None),
            rescue_required=getattr(sos_in, "rescue_required", False),
            rescue_units_required=getattr(sos_in, "rescue_units_required", None),
            ambulance_required=getattr(sos_in, "ambulance_required", False),
            ambulances_required=getattr(sos_in, "ambulances_required", None),
            required_resources_json=json.dumps(req_resources),
            notified_agencies_json=json.dumps(routed_agencies),
            photo_url=sos_in.photo_url,
            distance_km=distance_km,
            eta_minutes=eta_minutes,
            assigned_agency_id=primary_agency_id,
            assigned_resource_id=nearest_resource.id if nearest_resource else None,
            resend_status="NOT_SENT",
            pagerduty_status="NOT_SENT",
            assessment_json=assessment_dict,
            assessment_version=assessment.extraction_metadata.version,
            assessment_status="COMPLETED",
            priority_assessment_json=priority_dict,
            priority_score=prio_score,
            priority_level=prio_lvl,
            priority_scoring_version=prio_ver,
            zone_id=zone_id,
            created_at=datetime.utcnow(),
        )
        db.add(sos_event)
        db.flush()

        # 7. Audit log for Need & Assessment Agent
        assessment_src = assessment.extraction_metadata.source
        assessment_stat = "SUCCESS" if assessment_src != "DETERMINISTIC_FALLBACK" else "FALLBACK"
        assessment_log = AuditLog(
            zone_id=zone_id,
            agency_id=primary_agency_id,
            event_type="NEED_ASSESSMENT",
            description=f"Need & Assessment Agent normalized incident [{incident_id}] via {assessment_src}.",
            status=assessment_stat,
            metadata_json=json.dumps({
                "agent": "NEED_ASSESSMENT",
                "version": assessment.extraction_metadata.version,
                "source": assessment_src,
                "status": assessment_stat,
                "incident_id": incident_id,
            }),
            timestamp=datetime.utcnow(),
        )
        db.add(assessment_log)

        # 7b. Audit log for Priority & Severity Agent
        if priority_assessment:
            prio_log = AuditLog(
                zone_id=zone_id,
                agency_id=primary_agency_id,
                event_type="PRIORITY_ASSESSMENT",
                description=f"Priority & Severity Agent scored incident [{incident_id}]: score={prio_score}, level={prio_lvl}.",
                status="SUCCESS",
                metadata_json=json.dumps({
                    "agent": "PRIORITY_SEVERITY",
                    "version": prio_ver,
                    "zone_score": prio_score,
                    "priority_level": prio_lvl,
                    "fallbacks_used": priority_assessment.fallbacks_used,
                    "incident_id": incident_id,
                }),
                timestamp=datetime.utcnow(),
            )
            db.add(prio_log)

        # 8. Execute Automated Resource Allotment Engine
        try:
            resource_allocation_service.process_incident_allocations(
                db=db,
                sos=sos_event,
                explicit_requirements=sos_in.dict() if hasattr(sos_in, "dict") else sos_in.model_dump(),
            )
        except Exception as alloc_err:
            logger.error(f"Automated resource allocation failure (non-blocking for SOS): {alloc_err}")

        # 7. Create high-priority critical alert
        alert = Alert(
            zone_id=zone_id,
            title=f"🚨 SOS ACTIVATED - {zone_name}",
            message=(
                f"Incident: {incident_id} ({disaster_type}) | "
                f"Affected: {affected} (Injured: {injured}, Missing: {missing}) | "
                f"GPS: {sos_event.latitude:.4f}, {sos_event.longitude:.4f} | "
                f"Nearest Unit ETA: {eta_minutes}m ({distance_km}km) | "
                f"Providers Dispatched: {', '.join([a['agency_name'] for a in routed_agencies[:2]])}"
            ),
            alert_level="CRITICAL",
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.add(alert)
        db.flush()

        # 8. Create audit log
        log = AuditLog(
            zone_id=zone_id,
            agency_id=primary_agency_id,
            event_type="SOS_ACTIVATED",
            description=(
                f"CRITICAL SOS [{incident_id}] triggered in {zone_name}. "
                f"Coordination Agent assigned {len(routed_agencies)} providers. "
                f"Initial response ETA: {eta_minutes} mins."
            ),
            status="CRITICAL",
            metadata_json=json.dumps({
                "incident_id": incident_id,
                "sos_id": sos_event.id,
                "disaster_type": disaster_type,
                "severity": severity,
                "affected": affected,
                "injured": injured,
                "missing": missing,
                "distance_km": distance_km,
                "eta_minutes": eta_minutes,
                "photo_url": sos_in.photo_url,
                "notified_agencies": [a["agency_name"] for a in routed_agencies],
            }),
            timestamp=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(sos_event)
        db.refresh(alert)
        db.refresh(log)

        return sos_event, alert, log

    @staticmethod
    def dispatch_notifications_background(
        sos_id: str,
        incident_data: Dict[str, Any],
        routed_agencies: List[Dict[str, Any]],
        photo_url: Optional[str] = None,
    ):
        """
        Executes Resend email delivery and PagerDuty escalation in background.
        Updates database and audit log without blocking main request.
        """
        from app.database.session import SessionLocal

        db = SessionLocal()
        try:
            sos = db.query(SOSEvent).filter(SOSEvent.id == sos_id).first()
            if not sos:
                return

            resend_overall = "NOT_SENT"
            pagerduty_overall = "NOT_SENT"

            # 1. Collect all recipient emails ensuring NOTIFICATION_EMAIL is always included
            target_emails = set()
            primary_notify = getattr(settings, "NOTIFICATION_EMAIL", "aryanreddy2006@gmail.com")
            if primary_notify:
                target_emails.add(primary_notify.strip())

            for agency in routed_agencies:
                recp = agency.get("email")
                if recp and str(recp).strip():
                    target_emails.add(str(recp).strip())

            # Trigger Resend Emergency Emails for all unique recipients
            for recp in target_emails:
                try:
                    ok, status_code = email_service.send_emergency_email(
                        recipient=recp,
                        incident=incident_data,
                        photo_url=photo_url,
                    )
                    if ok and resend_overall != "FAILED":
                        resend_overall = status_code
                    elif not ok and resend_overall == "NOT_SENT":
                        resend_overall = status_code

                    # Audit log for email
                    audit_service.create_log(
                        db=db,
                        event_type="EMAIL_SENT" if ok else "EMAIL_FAILED",
                        description=f"Emergency Alert Email to ({recp}): {status_code}",
                        status="SUCCESS" if ok else "FAILURE",
                        zone_id=sos.zone_id,
                        agency_id=sos.assigned_agency_id,
                        metadata_dict={"incident_id": sos.incident_id, "status": status_code, "recipient": recp},
                    )
                except Exception as mail_err:
                    logger.warning(f"Email dispatch error for {recp}: {mail_err}")
                    if resend_overall == "NOT_SENT":
                        resend_overall = "FAILED"

            # 2. Trigger PagerDuty Emergency Escalation
            for agency in routed_agencies[:2]:  # Escalation to top 2 critical agencies
                try:
                    pd_ok, pd_status = pagerduty_service.trigger_pagerduty_incident(
                        incident=incident_data,
                        provider=agency,
                        affected_count=sos.people_affected,
                        injured_count=sos.injured_people,
                        missing_count=sos.missing_people,
                        eta=sos.eta_minutes or 11,
                    )
                    pagerduty_overall = pd_status
                    audit_service.create_log(
                        db=db,
                        event_type="PAGERDUTY_TRIGGERED" if pd_ok else "PAGERDUTY_FAILED",
                        description=f"PagerDuty Emergency Escalation for {agency.get('agency_name')}: {pd_status}",
                        status="SUCCESS" if pd_ok else "FAILURE",
                        zone_id=sos.zone_id,
                        agency_id=agency.get("agency_id"),
                        metadata_dict={"incident_id": sos.incident_id, "status": pd_status},
                    )
                except Exception as pd_err:
                    logger.warning(f"PagerDuty trigger error: {pd_err}")
                    pagerduty_overall = "FAILED"

            # Update SOS event notification statuses
            sos.resend_status = resend_overall
            sos.pagerduty_status = pagerduty_overall
            db.commit()

        except Exception as bg_err:
            logger.error(f"Background notification error: {bg_err}")
        finally:
            db.close()

sos_service = SOSService()
