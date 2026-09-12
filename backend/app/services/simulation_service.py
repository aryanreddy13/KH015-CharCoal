import json
import logging
import random
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import Zone, Resource, Allocation, Alert, AuditLog, Report
from app.websocket.connection_manager import manager
from app.services.audit_service import audit_service
from app.services.alert_service import alert_service
from app.schemas.schemas import AlertCreate

logger = logging.getLogger(__name__)

PAN_INDIA_SCENARIOS = [
    {
        "region_name": "Kerala Western Ghats (Wayanad Sector)",
        "zone_keyword": "Wayanad",
        "disaster_type": "Landslide",
        "severity": 9.8,
        "affected_people": 420,
        "injured_people": 58,
        "missing_people": 22,
        "latitude": 11.6854,
        "longitude": 76.1320,
        "reporter_name": "Wayanad Hill Rescue Cell",
        "contact": "+91-94471-20911",
        "description": "MASSIVE HILLSIDE LANDSLIDE: Cascading debris flows across Chooralmala and Meppadi hills in Wayanad. 420 plantation residents cut off, 58 injured, 22 buried under rubble. Heavy earthmovers, NDRF extrication teams, and trauma helicopters urgently required!",
        "required_resources": ["Rescue", "Medical", "Shelter"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Wayanad Ghat Pass (NH-766)",
            "message": "Massive rockfall and debris avalanche on NH-766 Thamarassery Ghat. Relief convoys delayed +30 min; rerouted via Kuttiyadi Pass.",
            "delay_minutes": 30,
        }
    },
    {
        "region_name": "Maharashtra Coastal Zone (Mumbai & Konkan)",
        "zone_keyword": "Mumbai",
        "disaster_type": "Flood",
        "severity": 9.5,
        "affected_people": 550,
        "injured_people": 46,
        "missing_people": 12,
        "latitude": 19.0760,
        "longitude": 72.8777,
        "reporter_name": "BMC Disaster Control Ward L",
        "contact": "+91-98200-55112",
        "description": "MONSOON URBAN INUNDATION: Arabian Sea high-tide surge exceeding 4.8m inundating Kurla, Mithi River, and Sion basins. 550 residents marooned on rooftops, 46 injured. Rapid inflatable boats and emergency food/water drops needed!",
        "required_resources": ["Rescue", "Food", "Water"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Western Express Highway & Milan Subway",
            "message": "Severe waterlogging over 4 feet at Milan Subway and WEH arterial bridge. Relief convoys rerouted via Eastern Freeway (+25 min delay).",
            "delay_minutes": 25,
        }
    },
    {
        "region_name": "Assam Brahmaputra Basin (Guwahati & Kaziranga)",
        "zone_keyword": "Assam",
        "disaster_type": "Flood",
        "severity": 9.7,
        "affected_people": 680,
        "injured_people": 64,
        "missing_people": 19,
        "latitude": 26.1445,
        "longitude": 91.7362,
        "reporter_name": "ASDMA Flood Relief Center",
        "contact": "+91-94350-88421",
        "description": "BRAHMAPUTRA EMBANKMENT BREACH: River flowing 2.4m above danger mark. Major breaches across Morigaon & Kamrup rural sectors. 680 villagers stranded on elevated bunds, 64 injured. Motorized relief boats, water purification kits, and emergency shelters required!",
        "required_resources": ["Rescue", "Medical", "Water", "Food"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Assam National Corridor (NH-27)",
            "message": "Floodwaters submerged 3km stretch of NH-27 near Jagiroad. Convoys diverted via North Bank Highway NH-15 (+35 min delay).",
            "delay_minutes": 35,
        }
    },
    {
        "region_name": "Odisha & West Bengal Coastal (Puri & Sundarbans)",
        "zone_keyword": "Odisha",
        "disaster_type": "Cyclone",
        "severity": 9.4,
        "affected_people": 480,
        "injured_people": 52,
        "missing_people": 15,
        "latitude": 19.8135,
        "longitude": 85.8312,
        "reporter_name": "ODRAF Coastal Outpost",
        "contact": "+91-94370-11209",
        "description": "SUPER CYCLONIC STORM SURGE: Gale winds of 150 km/h with 3.5m storm surges breached coastal saline embankments. 480 residents trapped in submerged delta villages, 52 injured. Amphibious craft, emergency trauma kits, and tarp shelters dispatched!",
        "required_resources": ["Rescue", "Shelter", "Medical"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Puri-Bhubaneswar Coastal Highway (NH-316)",
            "message": "Hundreds of uprooted coastal trees and fallen electricity pylons blocking NH-316. Clear-up squads deployed; convoy delay +20 min.",
            "delay_minutes": 20,
        }
    },
    {
        "region_name": "Uttarakhand Himalayan Ridge (Chamoli & Joshimath)",
        "zone_keyword": "Uttarakhand",
        "disaster_type": "Landslide",
        "severity": 9.2,
        "affected_people": 310,
        "injured_people": 39,
        "missing_people": 14,
        "latitude": 30.5526,
        "longitude": 79.5658,
        "reporter_name": "SDRF High-Altitude Command",
        "contact": "+91-94120-77334",
        "description": "HIMALAYAN CLOUDBURST & MUDSLIDE: Alaknanda valley flash flood coupled with upper ridge landslide. 310 pilgrims and locals trapped, 39 injured. Mountain rescue squads, trauma surgeons, and winter emergency shelters urgently needed!",
        "required_resources": ["Rescue", "Medical", "Shelter"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Badrinath National Highway (NH-58)",
            "message": "Massive boulder slide blocking NH-58 near Vishnuprayag gorge. Traffic halted; engineering teams clearing passage (+40 min delay).",
            "delay_minutes": 40,
        }
    },
    {
        "region_name": "Tamil Nadu Coastal Corridor (Chennai & Tambaram)",
        "zone_keyword": "Chennai",
        "disaster_type": "Flood",
        "severity": 8.9,
        "affected_people": 390,
        "injured_people": 31,
        "missing_people": 8,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "reporter_name": "Greater Chennai Emergency Taskforce",
        "contact": "+91-94440-66211",
        "description": "DELUGE INUNDATION: Adyar basin water levels surge past warning limits in Velachery & Tambaram. 390 marooned in ground-floor residences, 31 injured. Inflatable dinghies, clean potable water tankers, and medical aid requested!",
        "required_resources": ["Water", "Food", "Medical", "Rescue"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Grand Southern Trunk Road (GST Road)",
            "message": "Water accumulation over 3.5 ft on GST Road underpass near Airport. Convoys rerouted via Outer Ring Road (+20 min delay).",
            "delay_minutes": 20,
        }
    },
    {
        "region_name": "Central India Industrial Hub (Bhopal & Narmada Basin)",
        "zone_keyword": "Bhopal",
        "disaster_type": "Chemical Leak",
        "severity": 9.1,
        "affected_people": 340,
        "injured_people": 62,
        "missing_people": 5,
        "latitude": 23.2599,
        "longitude": 77.4126,
        "reporter_name": "State Emergency Response Team",
        "contact": "+91-98930-44551",
        "description": "INDUSTRIAL FLOOD INGRESS & HAZARDOUS RUNOFF: Industrial park chemical storage flooded following reservoir discharge. 340 affected by toxic fumes/inundation, 62 injured. Hazmat protection units and respiratory ambulances required!",
        "required_resources": ["Medical", "Rescue"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Bhopal-Indore State Highway (SH-18)",
            "message": "Bridge over Parbati river inundated by flash flood. Convoys diverted via NH-46 Sehore bypass (+25 min delay).",
            "delay_minutes": 25,
        }
    },
    {
        "region_name": "Northern Capital Region (Delhi Yamuna Riverfront)",
        "zone_keyword": "Delhi",
        "disaster_type": "Flood",
        "severity": 9.6,
        "affected_people": 350,
        "injured_people": 42,
        "missing_people": 11,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "reporter_name": "DDMA Emergency Control",
        "contact": "+91-98110-09921",
        "description": "YAMUNA RIVER SURGE: Embankment breach along Kashmere Gate & Monastery lowlands. 350 residents stranded, 42 injured, 11 swept in current. Rapid motorized boats and trauma ambulances deployed!",
        "required_resources": ["Rescue", "Medical"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Delhi Ring Road / Kashmere Gate Arterial",
            "message": "Yamuna backflow inundating Ring Road near ISBT. Convoys rerouted via Outer Ring Road & Barapullah (+20 min delay).",
            "delay_minutes": 20,
        }
    }
]

_scenario_cursor = 0

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
            description="Pan-India Multi-Agency Agentic Simulation Loop initialized across national disaster zones.",
            status="SUCCESS",
            metadata_dict={"simulation_state": "ACTIVE", "cycle": 1, "coverage": "Pan-India"},
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
            "message": "Pan-India AI Multi-Agent Coordinator Simulation has started.",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })

        return {
            "status": "success",
            "action": "START_SIMULATION",
            "message": "Pan-India Simulation started successfully. Disaster resources mobilized across all sectors.",
        }

    @staticmethod
    async def inject_emergency(db: Session, zone_id: str = None) -> Dict[str, Any]:
        """
        Simulates complete high-stakes emergency scenario across diverse Pan-India regions:
        (Wayanad Kerala, Mumbai Maharashtra, Brahmaputra Assam, Puri Odisha, Chamoli Uttarakhand, Chennai Tamil Nadu, Bhopal MP, Delhi NCR).
        Triggers SOS pipeline, Coordination routing, Notifications (Resend + PagerDuty), and real-time WebSockets.
        """
        global _scenario_cursor
        from app.services.sos_service import sos_service
        from app.schemas.schemas import SOSCreate

        # Pick scenario in rotation
        scenario = PAN_INDIA_SCENARIOS[_scenario_cursor % len(PAN_INDIA_SCENARIOS)]
        _scenario_cursor += 1

        # Locate matching zone or fallback to zone_id or closest/first zone
        target_zone = None
        if zone_id:
            target_zone = db.query(Zone).filter(Zone.id == zone_id).first()

        if not target_zone:
            # Try to match zone by keyword (e.g. Wayanad, Assam, Mumbai, etc.)
            target_zone = db.query(Zone).filter(Zone.name.ilike(f"%{scenario['zone_keyword']}%")).first()

        if not target_zone:
            # Try to match zone by matching disaster type or first available
            target_zone = db.query(Zone).filter(Zone.disaster_type.ilike(f"%{scenario['disaster_type']}%")).first() or db.query(Zone).first()

        if not target_zone:
            # Create a zone if none exists
            target_zone = Zone(
                name=f"Zone - {scenario['region_name']}",
                disaster_type=scenario["disaster_type"],
                latitude=scenario["latitude"],
                longitude=scenario["longitude"],
                overall_severity=scenario["severity"],
                affected_people=scenario["affected_people"],
                status="Critical",
            )
            db.add(target_zone)
            db.commit()
            db.refresh(target_zone)

        # Update Zone KPIs to match current high-stakes scenario
        target_zone.affected_people = scenario["affected_people"]
        target_zone.overall_severity = scenario["severity"]
        target_zone.disaster_type = scenario["disaster_type"]
        target_zone.status = "Critical"
        # Update coordinates to match the selected Indian sector if not already updated
        if abs(target_zone.latitude - scenario["latitude"]) > 0.5:
            target_zone.latitude = scenario["latitude"]
            target_zone.longitude = scenario["longitude"]
            target_zone.name = f"Zone - {scenario['region_name']}"

        db.commit()
        db.refresh(target_zone)

        evidence_photo = scenario["photo_url"]

        # Create SOS through complete pipeline
        sos_in = SOSCreate(
            reporter_name=scenario["reporter_name"],
            contact=scenario["contact"],
            latitude=scenario["latitude"] + 0.003,
            longitude=scenario["longitude"] - 0.002,
            accuracy=5.0,
            description=scenario["description"],
            disaster_type=scenario["disaster_type"],
            severity=scenario["severity"],
            people_affected=scenario["affected_people"],
            injured_people=scenario["injured_people"],
            missing_people=scenario["missing_people"],
            photo_url=evidence_photo,
            required_resources=scenario["required_resources"],
        )

        sos_event, alert, log = sos_service.create_sos(db, sos_in)

        # Parse routing
        routed_agencies = json.loads(sos_event.notified_agencies_json) if sos_event.notified_agencies_json else []
        req_res = json.loads(sos_event.required_resources_json) if sos_event.required_resources_json else scenario["required_resources"]

        incident_dict = {
            "id": sos_event.id,
            "incident_id": sos_event.incident_id,
            "disaster_type": scenario["disaster_type"],
            "zone_name": target_zone.name,
            "zone_id": target_zone.id,
            "severity": scenario["severity"],
            "location_text": f"{sos_event.latitude:.4f}, {sos_event.longitude:.4f} ({scenario['region_name']})",
            "latitude": sos_event.latitude,
            "longitude": sos_event.longitude,
            "accuracy": 5.0,
            "people_affected": scenario["affected_people"],
            "injured_people": scenario["injured_people"],
            "missing_people": scenario["missing_people"],
            "required_resources": req_res,
            "distance_km": sos_event.distance_km or 4.8,
            "eta_minutes": sos_event.eta_minutes or 11,
            "photo_url": evidence_photo,
            "provider_status": "NEW",
            "assigned_agency_id": sos_event.assigned_agency_id,
            "assigned_agency_name": sos_event.assigned_agency.name if sos_event.assigned_agency else "National Disaster Response Force",
            "assigned_resource_id": sos_event.assigned_resource_id,
            "assigned_resource_name": sos_event.assigned_resource.name if sos_event.assigned_resource else "Rapid Response Team",
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
            "latitude": target_zone.latitude,
            "longitude": target_zone.longitude,
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
            "region": scenario["region_name"],
            "incident_id": sos_event.incident_id,
            "new_severity": scenario["severity"],
            "affected_people": scenario["affected_people"],
            "injured_people": scenario["injured_people"],
            "missing_people": scenario["missing_people"],
            "routed_providers": [a["agency_name"] for a in routed_agencies],
            "photo_attached": True,
            "eta_minutes": sos_event.eta_minutes,
            "message": f"Emergency Injected in {scenario['region_name']} ({scenario['disaster_type']} - Severity {scenario['severity']})",
        }

    @staticmethod
    async def simulate_road_block(db: Session) -> Dict[str, Any]:
        """
        Simulates road blockage on key Indian transport arteries, updates allocation ETA, triggers warning alert.
        """
        allocation = db.query(Allocation).filter(Allocation.status == "EN_ROUTE").first()
        if not allocation:
            allocation = db.query(Allocation).first()

        if not allocation:
            return {"status": "error", "message": "No active allocations available to simulate road blockage."}

        # Pick a realistic Indian route blockage
        scenario = random.choice(PAN_INDIA_SCENARIOS)
        block_info = scenario.get("road_block", {
            "route_name": "National Highway Corridor (NH-44)",
            "message": "Major debris and waterlogging blocking national arterial corridor. Delay +25 min.",
            "delay_minutes": 25,
        })

        delay = block_info["delay_minutes"]
        allocation.status = "DELAYED"
        old_eta = allocation.eta_minutes or 10
        allocation.eta_minutes = old_eta + delay
        db.commit()
        db.refresh(allocation)

        # Create alert
        alert = Alert(
            zone_id=allocation.zone_id,
            title=f"Road Blockage: {block_info['route_name']}",
            message=f"{block_info['message']} Allocation for {allocation.resource.name if allocation.resource else 'Resource'} delayed by +{delay} min (Now: {allocation.eta_minutes} min).",
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
            description=f"Road blockage on {block_info['route_name']}. Allocation for {allocation.resource.name if allocation.resource else 'Resource'} delayed to {allocation.eta_minutes} mins.",
            status="WARNING",
            zone_id=allocation.zone_id,
            metadata_dict={"old_eta": old_eta, "new_eta": allocation.eta_minutes, "cause": "ROAD_BLOCK", "route": block_info["route_name"]},
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
            "delay_added": delay,
            "route": block_info["route_name"],
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
            "route": block_info["route_name"],
            "new_eta_minutes": allocation.eta_minutes,
            "message": f"Road blockage simulated on {block_info['route_name']}. ETA extended by {delay} mins (Now: {allocation.eta_minutes}m).",
        }

simulation_service = SimulationService()

