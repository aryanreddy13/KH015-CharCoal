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
        "region_name": "Kurla & Mithi River Basin (Central Mumbai)",
        "zone_keyword": "Kurla",
        "disaster_type": "Flood",
        "severity": 9.6,
        "affected_people": 580,
        "injured_people": 54,
        "missing_people": 16,
        "latitude": 19.0657,
        "longitude": 72.8780,
        "reporter_name": "BMC Disaster Management Ward L (Kurla)",
        "contact": "+91-98200-55112",
        "description": "MITHI RIVER OVERFLOW & KURLA DELUGE: Intense 120mm/hr rainfall during 4.8m Arabian Sea high-tide causing Mithi River to breach banks at Kranti Nagar and Bail Bazar. Over 580 residents marooned in low-lying chawls, 54 injured. Rapid inflatable boats and potable water units urgently required!",
        "required_resources": ["Rescue", "Water", "Food", "Medical"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "LBS Marg & Kurla Depot Junction",
            "message": "Floodwaters over 4.2 feet on Lal Bahadur Shastri (LBS) Marg near Kurla Station. Relief convoys diverted via Santacruz-Chembur Link Road (+20 min delay).",
            "delay_minutes": 20,
        }
    },
    {
        "region_name": "Hindmata, Dadar & Parel Bowl (South-Central Mumbai)",
        "zone_keyword": "Dadar",
        "disaster_type": "Flood",
        "severity": 9.3,
        "affected_people": 420,
        "injured_people": 38,
        "missing_people": 6,
        "latitude": 19.0178,
        "longitude": 72.8478,
        "reporter_name": "Mumbai Fire Brigade HQ (Byculla/Dadar)",
        "contact": "+91-98199-33211",
        "description": "HINDMATA FLYOVER & DADAR SUBMERGENCE: Heavy waterlogging in chronic depression bowl. Dr. Babasaheb Ambedkar Road impassable with 4.5 feet water. KEM & Tata Memorial emergency hospital corridors restricted. High-capacity dewatering pumps and ambulances needed!",
        "required_resources": ["Medical", "Rescue", "Ambulance"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Dr. Ambedkar Road / Hindmata Underpass",
            "message": "Hindmata underpass completely inundated. Emergency convoys rerouted via Senapati Bapat Marg & Eastern Freeway (+25 min delay).",
            "delay_minutes": 25,
        }
    },
    {
        "region_name": "Malad & Sanjay Gandhi Hillside (Western Suburbs)",
        "zone_keyword": "Malad",
        "disaster_type": "Landslide",
        "severity": 9.7,
        "affected_people": 350,
        "injured_people": 62,
        "missing_people": 21,
        "latitude": 19.1860,
        "longitude": 72.8485,
        "reporter_name": "NDRF Unit 5 Sub-Depot (Malad)",
        "contact": "+91-98330-11922",
        "description": "APPAPADA & MALAD QUARRY HILLSIDE COLLAPSE: Torrential downpour caused catastrophic slope failure and retaining wall collapse into hillside settlements. 350 trapped, 62 injured, 21 buried under debris. Heavy earthmovers, canine search teams, and ICU trauma vans needed!",
        "required_resources": ["Rescue", "Medical", "Shelter"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Western Express Highway (WEH) Malad Flyover",
            "message": "Mudslide debris and fallen trees on WEH Northbound near Pushpa Park. Convoys diverted via Link Road (+30 min delay).",
            "delay_minutes": 30,
        }
    },
    {
        "region_name": "Andheri Subway & Western Corridor (Western Mumbai)",
        "zone_keyword": "Andheri",
        "disaster_type": "Flood",
        "severity": 9.1,
        "affected_people": 310,
        "injured_people": 28,
        "missing_people": 4,
        "latitude": 19.1136,
        "longitude": 72.8697,
        "reporter_name": "Western Railway Emergency Desk",
        "contact": "+91-98210-44910",
        "description": "ANDHERI SUBWAY & SV ROAD DELUGE: Milan and Andheri subway underpasses submerged under 6 feet of water, trapping public transit buses. 310 commuters marooned, 28 injured. Mobile crane recovery and rescue boats deployed!",
        "required_resources": ["Rescue", "Ambulance", "Water"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Milan Subway & SV Road Underpass",
            "message": "Milan Subway impassable due to 5.5ft floodwater. Convoys rerouted via Captain Gore Flyover (+18 min delay).",
            "delay_minutes": 18,
        }
    },
    {
        "region_name": "Ghatkopar & LBS Marg Industrial Zone (Eastern Suburbs)",
        "zone_keyword": "Ghatkopar",
        "disaster_type": "Chemical Leak",
        "severity": 9.4,
        "affected_people": 460,
        "injured_people": 74,
        "missing_people": 8,
        "latitude": 19.0860,
        "longitude": 72.9090,
        "reporter_name": "MIDC Industrial Emergency Response",
        "contact": "+91-98700-66440",
        "description": "INDUSTRIAL FLOOD INGRESS & HAZMAT RUNOFF: Flash flood inundated chemical storage facilities on LBS Marg near Pant Nagar. 460 workers/residents affected by toxic chemical vapor, 74 injured with respiratory distress. Hazmat decontamination and specialized respiratory ambulances needed!",
        "required_resources": ["Medical", "Rescue", "Water"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Eastern Express Highway (EEH) Chedda Nagar",
            "message": "Hazardous spill and deep waterlogging on EEH Southbound near Ghatkopar flyover. Convoys rerouted via Sion-Trombay Road (+25 min delay).",
            "delay_minutes": 25,
        }
    },
    {
        "region_name": "Colaba, Marine Drive & Coastal Sector (South Mumbai)",
        "zone_keyword": "Colaba",
        "disaster_type": "Cyclone",
        "severity": 9.2,
        "affected_people": 290,
        "injured_people": 34,
        "missing_people": 5,
        "latitude": 18.9220,
        "longitude": 72.8347,
        "reporter_name": "Indian Coast Guard Western Command",
        "contact": "+91-98200-99881",
        "description": "COASTAL SURGE & PROMENADE BREACH: 5.2m Arabian Sea high-tide waves crashing over Marine Drive and Sassoon Docks. Fishermen boats capsized, ground floors inundated in Colaba. Emergency shelters and sea rescue crafts active!",
        "required_resources": ["Rescue", "Shelter", "Medical"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Bandra-Worli Sea Link & Marine Drive",
            "message": "Bandra-Worli Sea Link closed due to 85 km/h crosswinds and sea spray. Convoys diverted via Mahim Causeway & Senapati Bapat Marg (+22 min delay).",
            "delay_minutes": 22,
        }
    },
    {
        "region_name": "Bandra-Kurla Complex (BKC) & Dharavi (Central Corridor)",
        "zone_keyword": "Bandra",
        "disaster_type": "Flood",
        "severity": 9.0,
        "affected_people": 510,
        "injured_people": 41,
        "missing_people": 9,
        "latitude": 19.0550,
        "longitude": 72.8550,
        "reporter_name": "Dharavi Community Relief Desk",
        "contact": "+91-98190-77112",
        "description": "DHARAVI & BKC WATERLOGGING: Water levels exceeding 3.8 feet in 90 Feet Road & Transit Camp. Over 510 residents in dense settlements require immediate evacuation. Food packets, dry rations, and clean drinking water tankers needed!",
        "required_resources": ["Food", "Water", "Rescue", "Medical"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "BKC Connector & Sion-Bandra Link Road",
            "message": "Waterlogging at BKC Connector entry ramp. Convoys rerouted via Dharavi Main Road (+15 min delay).",
            "delay_minutes": 15,
        }
    },
    {
        "region_name": "Thane Creek & Ghodbunder Corridor (MMR Sector)",
        "zone_keyword": "Thane",
        "disaster_type": "Landslide",
        "severity": 8.8,
        "affected_people": 270,
        "injured_people": 32,
        "missing_people": 7,
        "latitude": 19.2183,
        "longitude": 72.9781,
        "reporter_name": "TMC Regional Disaster Management Cell",
        "contact": "+91-98200-88334",
        "description": "GHODBUNDER GHAT ROCKFALL: Major rockslip on Ghodbunder Road hills blocking vital corridor between Thane, Western Suburbs, and Gujarat. 270 vehicles stranded, 32 injured. Heavy hydraulic cranes and trauma vans on scene!",
        "required_resources": ["Rescue", "Medical", "Ambulance"],
        "photo_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
        "road_block": {
            "route_name": "Ghodbunder Road (SH-42) Ghat Section",
            "message": "Massive boulder on Ghodbunder Ghat near Gaimukh. Traffic diverted via Eastern Express Highway & Thane Majiwada (+35 min delay).",
            "delay_minutes": 35,
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

