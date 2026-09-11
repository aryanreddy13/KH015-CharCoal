import json
import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Zone, Resource, Allocation, Alert, AuditLog, Report
from app.websocket.connection_manager import manager
from app.services.audit_service import audit_service
from app.services.alert_service import alert_service
from app.schemas.schemas import AlertCreate

logger = logging.getLogger(__name__)

class SimulationService:
    @staticmethod
    async def start_simulation(db: Session) -> Dict[str, Any]:
        """
        Activates real-time response simulation: shifts resource statuses, adds audit trail.
        """
        # Update an available resource to ALLOCATED or EN_ROUTE
        available_res = db.query(Resource).filter(Resource.status == "AVAILABLE").first()
        if available_res:
            available_res.status = "ALLOCATED"
            db.commit()
            db.refresh(available_res)

            await manager.broadcast("RESOURCE_UPDATED", {
                "resource_id": available_res.id,
                "name": available_res.name,
                "status": available_res.status,
            })

        log = audit_service.create_log(
            db=db,
            event_type="SIMULATION_TRIGGERED",
            description="Agentic Simulation Loop initialized across 5 disaster zones.",
            status="SUCCESS",
            metadata_dict={"simulation_state": "ACTIVE", "cycle": 1},
        )

        await manager.broadcast("AUDIT_LOG_CREATED", {
            "id": log.id,
            "event_type": log.event_type,
            "description": log.description,
            "status": log.status,
            "timestamp": log.timestamp.isoformat() + "Z",
        })

        await manager.broadcast("SIMULATION_EVENT", {
            "action": "START_SIMULATION",
            "message": "Real-time AI Multi-Agent Coordinator Simulation has started.",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })

        return {
            "status": "success",
            "action": "START_SIMULATION",
            "message": "Simulation started successfully. Resources mobilized and live feeds initiated.",
        }

    @staticmethod
    async def inject_emergency(db: Session, zone_id: str = None) -> Dict[str, Any]:
        """
        Simulates complete high-stakes emergency scenario:
        Zone A | Flood | Severity 9.8 | 350 Affected | 42 Injured | 11 Missing | Rescue + Medical | Photo
        Triggers SOS pipeline, Coordination routing, Notifications (Resend + PagerDuty), and real-time WebSockets.
        """
        from app.services.sos_service import sos_service
        from app.schemas.schemas import SOSCreate

        target_zone = None
        if zone_id:
            target_zone = db.query(Zone).filter(Zone.id == zone_id).first()
        if not target_zone:
            target_zone = db.query(Zone).filter(Zone.name.like("%Zone A%")).first() or db.query(Zone).first()

        if not target_zone:
            return {"status": "error", "message": "No active zones found to inject emergency."}

        # Update Zone KPIs
        target_zone.affected_people = 350
        target_zone.overall_severity = 9.8
        target_zone.status = "Critical"
        db.commit()
        db.refresh(target_zone)

        # Realistic disaster evidence photo (public high-res flood rescue image)
        evidence_photo = "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80"

        # Create SOS through complete pipeline
        sos_in = SOSCreate(
            reporter_name="Citizen Emergency Ward 4",
            contact="+91-98110-09921",
            latitude=target_zone.latitude + 0.003,
            longitude=target_zone.longitude - 0.002,
            accuracy=5.0,
            description="CRITICAL FLOOD SURGE: Embankment collapse along Riverfront Sector 4. Over 350 residents stranded on rooftops, 42 injured, 11 swept in current. Rapid rescue boats and trauma ambulances urgently required!",
            disaster_type="Flood",
            severity=9.8,
            people_affected=350,
            injured_people=42,
            missing_people=11,
            photo_url=evidence_photo,
            required_resources=["Rescue", "Medical"],
        )

        sos_event, alert, log = sos_service.create_sos(db, sos_in)

        # Parse routing
        routed_agencies = json.loads(sos_event.notified_agencies_json) if sos_event.notified_agencies_json else []
        req_res = json.loads(sos_event.required_resources_json) if sos_event.required_resources_json else ["Rescue", "Medical"]

        incident_dict = {
            "id": sos_event.id,
            "incident_id": sos_event.incident_id,
            "disaster_type": "Flood",
            "zone_name": target_zone.name,
            "zone_id": target_zone.id,
            "severity": 9.8,
            "location_text": f"{sos_event.latitude:.4f}, {sos_event.longitude:.4f}",
            "latitude": sos_event.latitude,
            "longitude": sos_event.longitude,
            "accuracy": 5.0,
            "people_affected": 350,
            "injured_people": 42,
            "missing_people": 11,
            "required_resources": req_res,
            "distance_km": sos_event.distance_km or 4.8,
            "eta_minutes": sos_event.eta_minutes or 11,
            "photo_url": evidence_photo,
            "provider_status": "NEW",
            "assigned_agency_id": sos_event.assigned_agency_id,
            "assigned_agency_name": sos_event.assigned_agency.name if sos_event.assigned_agency else "Fire & Rescue Department",
            "assigned_resource_id": sos_event.assigned_resource_id,
            "assigned_resource_name": sos_event.assigned_resource.name if sos_event.assigned_resource else "Rapid Water Rescue Team 01",
            "resend_status": "SENT",
            "pagerduty_status": "SENT",
            "created_at": sos_event.created_at.isoformat() + "Z",
        }

        # Dispatch background notifications
        import asyncio
        asyncio.create_task(asyncio.to_thread(
            sos_service.dispatch_notifications_background,
            sos_id=sos_event.id,
            incident_data=incident_dict,
            routed_agencies=routed_agencies,
            photo_url=evidence_photo,
        ))

        # Broadcast real-time WebSockets
        await manager.broadcast("ZONE_UPDATED", {
            "zone_id": target_zone.id,
            "name": target_zone.name,
            "severity": target_zone.overall_severity,
            "affected_people": target_zone.affected_people,
            "status": target_zone.status,
        })

        await manager.broadcast("SOS_ACTIVATED", incident_dict)
        await manager.broadcast("PROVIDER_INCIDENT_CREATED", incident_dict)

        await manager.broadcast("ALERT_CREATED", {
            "id": alert.id,
            "zone_id": alert.zone_id,
            "title": alert.title,
            "message": alert.message,
            "alert_level": alert.alert_level,
        })

        await manager.broadcast("AUDIT_LOG_CREATED", {
            "id": log.id,
            "event_type": log.event_type,
            "description": log.description,
            "status": log.status,
            "timestamp": log.timestamp.isoformat() + "Z",
        })

        return {
            "status": "success",
            "action": "INJECT_EMERGENCY",
            "zone": target_zone.name,
            "incident_id": sos_event.incident_id,
            "new_severity": 9.8,
            "affected_people": 350,
            "injured_people": 42,
            "missing_people": 11,
            "routed_providers": [a["agency_name"] for a in routed_agencies],
            "photo_attached": True,
            "eta_minutes": sos_event.eta_minutes,
        }

    @staticmethod
    async def simulate_road_block(db: Session) -> Dict[str, Any]:
        """
        Simulates road blockage, updates allocation ETA, triggers warning alert.
        """
        allocation = db.query(Allocation).filter(Allocation.status == "EN_ROUTE").first()
        if not allocation:
            allocation = db.query(Allocation).first()

        if not allocation:
            return {"status": "error", "message": "No active allocations available to simulate road blockage."}

        # Update ETA and mark as DELAYED
        allocation.status = "DELAYED"
        old_eta = allocation.eta_minutes or 10
        allocation.eta_minutes = old_eta + 25
        db.commit()
        db.refresh(allocation)

        # Create alert
        alert = Alert(
            zone_id=allocation.zone_id,
            title="Road Blockage Detected on Arterial Route",
            message=f"Debris / flood waterlogging on NH-24 has blocked route for {allocation.resource.name if allocation.resource else 'Resource'}. ETA delayed by +25 min (Now: {allocation.eta_minutes} min).",
            alert_level="WARNING",
            is_active=True,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Audit log
        log = audit_service.create_log(
            db=db,
            event_type="ETA_UPDATED",
            description=f"Road blockage on primary corridor. Allocation for {allocation.resource.name if allocation.resource else 'Resource'} delayed to {allocation.eta_minutes} mins.",
            status="WARNING",
            zone_id=allocation.zone_id,
            metadata_dict={"old_eta": old_eta, "new_eta": allocation.eta_minutes, "cause": "ROAD_BLOCK"},
        )

        # Broadcasts
        await manager.broadcast("ALLOCATION_UPDATED", {
            "allocation_id": allocation.id,
            "status": allocation.status,
            "eta_minutes": allocation.eta_minutes,
        })

        await manager.broadcast("ETA_UPDATED", {
            "allocation_id": allocation.id,
            "new_eta": allocation.eta_minutes,
            "delay_added": 25,
        })

        await manager.broadcast("ALERT_CREATED", {
            "id": alert.id,
            "zone_id": alert.zone_id,
            "title": alert.title,
            "message": alert.message,
            "alert_level": alert.alert_level,
        })

        await manager.broadcast("AUDIT_LOG_CREATED", {
            "id": log.id,
            "event_type": log.event_type,
            "description": log.description,
            "status": log.status,
            "timestamp": log.timestamp.isoformat() + "Z",
        })

        return {
            "status": "success",
            "action": "SIMULATE_ROAD_BLOCK",
            "allocation_id": allocation.id,
            "new_eta_minutes": allocation.eta_minutes,
            "message": f"Road blockage simulated. ETA extended by 25 minutes to {allocation.eta_minutes}m.",
        }

simulation_service = SimulationService()
