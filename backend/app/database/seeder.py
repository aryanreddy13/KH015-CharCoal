import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import (
    User,
    Agency,
    Zone,
    Need,
    Resource,
    Allocation,
    Alert,
    AuditLog,
    Report,
)

logger = logging.getLogger(__name__)

def seed_database(db: Session):
    from app.config import settings

    # Ensure all 5 Provider Agencies exist and have up-to-date contact details
    agencies_data = [
        {"name": "Fire & Rescue Department", "type": "FIRE_RESCUE", "contact_number": settings.FIRE_EMERGENCY_NUMBER, "email": settings.FIRE_EMERGENCY_EMAIL},
        {"name": "City Medical Response", "type": "MEDICAL", "contact_number": settings.MEDICAL_EMERGENCY_NUMBER, "email": settings.MEDICAL_EMERGENCY_EMAIL},
        {"name": "Metropolitan Police Department", "type": "POLICE", "contact_number": None, "email": None},
        {"name": "NGO Alpha Relief", "type": "NGO", "contact_number": settings.NGO_EMERGENCY_NUMBER, "email": settings.NGO_EMERGENCY_EMAIL},
        {"name": "Government Emergency Services", "type": "GOVERNMENT", "contact_number": "+91-108-555-0105", "email": "state.emergency@ps20-gov.in"},
    ]
    agency_objs = {}
    for item in agencies_data:
        existing_ag = db.query(Agency).filter((Agency.type == item["type"]) | (Agency.name == item["name"])).first()
        if not existing_ag:
            new_ag = Agency(name=item["name"], type=item["type"], contact_number=item["contact_number"], email=item["email"], status="ACTIVE")
            db.add(new_ag)
            db.flush()
            agency_objs[item["type"]] = new_ag
            agency_objs[item["name"]] = new_ag
        else:
            existing_ag.contact_number = item["contact_number"]
            existing_ag.email = item["email"]
            if existing_ag.type != item["type"]:
                existing_ag.type = item["type"]
            agency_objs[item["type"]] = existing_ag
            agency_objs[item["name"]] = existing_ag
    db.commit()

    # Fixed Primary Inventory Resources per specifications:
    # NGO: FOOD (500), WATER (1000), SHELTER (100), MEDICINE (250)
    # FIRE: RESCUE (10)
    # MEDICAL: AMBULANCE (8)
    primary_inventory = [
        {"agency_type": "NGO", "resource_type": "FOOD", "name": "Emergency Food Kits", "total": 500, "unit": "Kits", "lat": 28.6800, "lng": 77.1500},
        {"agency_type": "NGO", "resource_type": "WATER", "name": "Potable Water Units", "total": 1000, "unit": "Units", "lat": 28.6700, "lng": 77.1600},
        {"agency_type": "NGO", "resource_type": "SHELTER", "name": "Emergency Shelter Spaces", "total": 100, "unit": "Spaces", "lat": 28.6600, "lng": 77.1300},
        {"agency_type": "NGO", "resource_type": "MEDICINE", "name": "Trauma Medicine Kits", "total": 250, "unit": "Kits", "lat": 28.5600, "lng": 77.2100},
        {"agency_type": "FIRE_RESCUE", "resource_type": "RESCUE", "name": "Rapid Water & Extrication Rescue Units", "total": 10, "unit": "Units", "lat": 28.6300, "lng": 77.2150},
        {"agency_type": "MEDICAL", "resource_type": "AMBULANCE", "name": "Emergency ICU Ambulances", "total": 8, "unit": "Ambulances", "lat": 28.5700, "lng": 77.2200},
    ]

    from sqlalchemy import func

    for inv in primary_inventory:
        ag = agency_objs.get(inv["agency_type"])
        if not ag:
            continue
        existing_res = db.query(Resource).filter(
            Resource.agency_id == ag.id,
            (func.upper(Resource.resource_type) == inv["resource_type"].upper()) | (Resource.name == inv["name"])
        ).first()
        if not existing_res:
            new_res = Resource(
                agency_id=ag.id,
                name=inv["name"],
                resource_type=inv["resource_type"],
                quantity=inv["total"],
                total_quantity=inv["total"],
                available_quantity=inv["total"],
                reserved_quantity=0,
                allocated_quantity=0,
                unit=inv["unit"],
                location="Central Regional Depot",
                latitude=inv["lat"],
                longitude=inv["lng"],
                status="AVAILABLE",
            )
            db.add(new_res)
            db.flush()
        else:
            # Sync total and available if needed
            existing_res.name = inv["name"]
            existing_res.resource_type = inv["resource_type"]
            existing_res.unit = inv["unit"]
            existing_res.total_quantity = inv["total"]
            if existing_res.available_quantity is None or existing_res.available_quantity <= 1:
                existing_res.available_quantity = inv["total"]
            existing_res.quantity = inv["total"]
            existing_res.status = "AVAILABLE"
    db.commit()


    # Check if full database is already seeded
    existing_zones_count = db.query(Zone).count()
    if existing_zones_count > 0:
        logger.info(f"Database already contains {existing_zones_count} zones. Skipping seed.")
        return

    logger.info("Starting database seed with 5 zones, agencies, resources, allocations, and alerts...")

    agency_objs = {a.name: a for a in db.query(Agency).all()}

    # 2. Users
    commander = User(
        name="Commander Sarah Vance",
        email="commander@emergency.gov",
        role="COMMANDER",
        agency_id=agency_objs["Government Emergency Services"].id,
    )
    db.add(commander)
    db.flush()

    # 3. Exactly 5 Zones
    # ZONE A: Flood, Severity 9.6, 350 affected, Critical, Rescue 9.8, Medical 9.4, Food 7.1
    # ZONE B: Earthquake, Severity 9.1, 280 affected, Critical, Medical 9.5, Shelter 9.0
    # ZONE C: Flood, Severity 7.4, 150 affected, High, Food 7.8, Water 7.2
    # ZONE D: Cyclone, Severity 5.8, 100 affected, Moderate, Shelter 6.0, Medical 5.5
    # ZONE E: Flood, Severity 3.2, 50 affected, Low, Food 3.5, Water 3.0

    zones_info = [
        {
            "key": "ZONE_A",
            "name": "Zone A - Riverfront & Central Metro",
            "disaster_type": "Flood",
            "overall_severity": 9.6,
            "affected_people": 350,
            "status": "Critical",
            "lat": 28.6139,
            "lng": 77.2090,
            "needs": [
                {"resource_type": "Rescue", "qty_req": 25, "qty_ful": 10, "sev": 9.8, "pri": 9.8, "status": "CRITICAL"},
                {"resource_type": "Medical", "qty_req": 20, "qty_ful": 8, "sev": 9.4, "pri": 9.4, "status": "CRITICAL"},
                {"resource_type": "Food", "qty_req": 100, "qty_ful": 40, "sev": 7.1, "pri": 7.1, "status": "IN_PROGRESS"},
            ],
        },
        {
            "key": "ZONE_B",
            "name": "Zone B - Foothills & Industrial Belt",
            "disaster_type": "Earthquake",
            "overall_severity": 9.1,
            "affected_people": 280,
            "status": "Critical",
            "lat": 28.5355,
            "lng": 77.3910,
            "needs": [
                {"resource_type": "Medical", "qty_req": 30, "qty_ful": 12, "sev": 9.5, "pri": 9.5, "status": "CRITICAL"},
                {"resource_type": "Shelter", "qty_req": 40, "qty_ful": 15, "sev": 9.0, "pri": 9.0, "status": "CRITICAL"},
            ],
        },
        {
            "key": "ZONE_C",
            "name": "Zone C - Coastal Highway Corridor",
            "disaster_type": "Flood",
            "overall_severity": 7.4,
            "affected_people": 150,
            "status": "High",
            "lat": 28.7041,
            "lng": 77.1025,
            "needs": [
                {"resource_type": "Food", "qty_req": 60, "qty_ful": 20, "sev": 7.8, "pri": 7.8, "status": "IN_PROGRESS"},
                {"resource_type": "Water", "qty_req": 80, "qty_ful": 30, "sev": 7.2, "pri": 7.2, "status": "IN_PROGRESS"},
            ],
        },
        {
            "key": "ZONE_D",
            "name": "Zone D - Eastern Ridge Communities",
            "disaster_type": "Cyclone",
            "overall_severity": 5.8,
            "affected_people": 100,
            "status": "Moderate",
            "lat": 28.4595,
            "lng": 77.0266,
            "needs": [
                {"resource_type": "Shelter", "qty_req": 20, "qty_ful": 10, "sev": 6.0, "pri": 6.0, "status": "IN_PROGRESS"},
                {"resource_type": "Medical", "qty_req": 15, "qty_ful": 8, "sev": 5.5, "pri": 5.5, "status": "IN_PROGRESS"},
            ],
        },
        {
            "key": "ZONE_E",
            "name": "Zone E - South Agricultural District",
            "disaster_type": "Flood",
            "overall_severity": 3.2,
            "affected_people": 50,
            "status": "Low",
            "lat": 28.6692,
            "lng": 77.4538,
            "needs": [
                {"resource_type": "Food", "qty_req": 30, "qty_ful": 20, "sev": 3.5, "pri": 3.5, "status": "IN_PROGRESS"},
                {"resource_type": "Water", "qty_req": 40, "qty_ful": 30, "sev": 3.0, "pri": 3.0, "status": "IN_PROGRESS"},
            ],
        },
    ]

    zone_objs = {}
    need_objs = {}

    for z_data in zones_info:
        zone = Zone(
            name=z_data["name"],
            disaster_type=z_data["disaster_type"],
            latitude=z_data["lat"],
            longitude=z_data["lng"],
            overall_severity=z_data["overall_severity"],
            affected_people=z_data["affected_people"],
            status=z_data["status"],
        )
        db.add(zone)
        db.flush()
        zone_objs[z_data["key"]] = zone

        for n_data in z_data["needs"]:
            need = Need(
                zone_id=zone.id,
                resource_type=n_data["resource_type"],
                quantity_required=n_data["qty_req"],
                quantity_fulfilled=n_data["qty_ful"],
                severity=n_data["sev"],
                priority_score=n_data["pri"],
                status=n_data["status"],
            )
            db.add(need)
            db.flush()
            need_objs[f"{z_data['key']}_{n_data['resource_type']}"] = need

    # 4. Resources distributed across agencies
    resources_data = [
        # Fire & Rescue
        {
            "agency": "Fire & Rescue Department",
            "name": "Rapid Water Rescue Team 01",
            "type": "Rescue",
            "qty": 5,
            "lat": 28.6300,
            "lng": 77.2150,
            "status": "AVAILABLE",
            "capacity": "5 Heavy Inflatable Rafts & 15 Crew",
        },
        {
            "agency": "Fire & Rescue Department",
            "name": "Urban Search & Rescue Team 02",
            "type": "Rescue",
            "qty": 8,
            "lat": 28.6200,
            "lng": 77.1950,
            "status": "ALLOCATED",
            "capacity": "8 Structural Collapse Specialists",
        },
        # City Medical Response
        {
            "agency": "City Medical Response",
            "name": "Mobile Trauma Hospital Unit 01",
            "type": "Medical",
            "qty": 4,
            "lat": 28.5700,
            "lng": 77.2200,
            "status": "AVAILABLE",
            "capacity": "4 ICU Ambulances + Triage Tents",
        },
        {
            "agency": "City Medical Response",
            "name": "Emergency Critical Care Team Alpha",
            "type": "Medical",
            "qty": 6,
            "lat": 28.5500,
            "lng": 77.2800,
            "status": "EN_ROUTE",
            "capacity": "12 Paramedics & Emergency Doctors",
        },
        {
            "agency": "City Medical Response",
            "name": "Trauma Medicine Supply Pack A",
            "type": "Medicine",
            "qty": 200,
            "lat": 28.5600,
            "lng": 77.2100,
            "status": "AVAILABLE",
            "capacity": "200 Comprehensive Trauma Surgery Kits",
        },
        # NGO Alpha
        {
            "agency": "NGO Alpha Relief",
            "name": "Emergency Food Supply Convoy Alpha",
            "type": "Food",
            "qty": 500,
            "lat": 28.6800,
            "lng": 77.1500,
            "status": "AVAILABLE",
            "capacity": "500 Dry Ready-to-Eat Ration Boxes",
        },
        {
            "agency": "NGO Alpha Relief",
            "name": "Potable Water Tanker Fleet (5000L)",
            "type": "Water",
            "qty": 10,
            "lat": 28.6700,
            "lng": 77.1600,
            "status": "EN_ROUTE",
            "capacity": "10x 5000 Liters Purified Water Tankers",
        },
        {
            "agency": "NGO Alpha Relief",
            "name": "All-Weather Family Shelter Tents",
            "type": "Shelter",
            "qty": 50,
            "lat": 28.6600,
            "lng": 77.1300,
            "status": "AVAILABLE",
            "capacity": "50 Heavy-Duty 6-Person Weatherproof Tents",
        },
        # Metropolitan Police Department
        {
            "agency": "Metropolitan Police Department",
            "name": "Tactical Evacuation & Perimeter Unit 01",
            "type": "Rescue",
            "qty": 8,
            "lat": 28.5900,
            "lng": 28.5900,
            "status": "AVAILABLE",
            "capacity": "8 Tactical Officers, Crowd Barriers & Drones",
        },
        {
            "agency": "Metropolitan Police Department",
            "name": "Emergency Highway Corridor Patrol 03",
            "type": "Rescue",
            "qty": 4,
            "lat": 28.6500,
            "lng": 77.2400,
            "status": "AVAILABLE",
            "capacity": "4 High-Mobility Interceptors & Satellite Comms",
        },
        # Government Emergency Services
        {
            "agency": "Government Emergency Services",
            "name": "National Disaster Response Unit 04",
            "type": "Rescue",
            "qty": 12,
            "lat": 28.6000,
            "lng": 77.3000,
            "status": "ALLOCATED",
            "capacity": "12 NDRF Specialist Operatives & Drones",
        },
        {
            "agency": "Government Emergency Services",
            "name": "Modular Emergency Shelter Pods",
            "type": "Shelter",
            "qty": 80,
            "lat": 28.6100,
            "lng": 77.3200,
            "status": "AVAILABLE",
            "capacity": "80 Rapid Assembly Aluminum-Frame Pods",
        },
    ]

    resource_objs = {}
    for r_data in resources_data:
        agency = agency_objs[r_data["agency"]]
        resource = Resource(
            agency_id=agency.id,
            name=r_data["name"],
            resource_type=r_data["type"],
            quantity=r_data["qty"],
            latitude=r_data["lat"],
            longitude=r_data["lng"],
            status=r_data["status"],
            capacity=r_data["capacity"],
        )
        db.add(resource)
        db.flush()
        resource_objs[r_data["name"]] = resource

    # 5. Allocations
    allocations_data = [
        {
            "resource": "Urban Search & Rescue Team 02",
            "zone": "ZONE_A",
            "need": "ZONE_A_Rescue",
            "qty": 8,
            "status": "EN_ROUTE",
            "dist": 4.2,
            "eta": 8,
        },
        {
            "resource": "Emergency Critical Care Team Alpha",
            "zone": "ZONE_A",
            "need": "ZONE_A_Medical",
            "qty": 6,
            "status": "EN_ROUTE",
            "dist": 7.5,
            "eta": 14,
        },
        {
            "resource": "First-Aid Surgical Kits Beta",
            "zone": "ZONE_B",
            "need": "ZONE_B_Medical",
            "qty": 40,
            "status": "EN_ROUTE",
            "dist": 11.2,
            "eta": 22,
        },
        {
            "resource": "Potable Water Tanker Fleet (5000L)",
            "zone": "ZONE_C",
            "need": "ZONE_C_Water",
            "qty": 5,
            "status": "EN_ROUTE",
            "dist": 5.8,
            "eta": 12,
        },
    ]

    for a_data in allocations_data:
        res = resource_objs[a_data["resource"]]
        zn = zone_objs[a_data["zone"]]
        nd = need_objs.get(a_data["need"])
        alloc = Allocation(
            resource_id=res.id,
            zone_id=zn.id,
            need_id=nd.id if nd else None,
            quantity=a_data["qty"],
            status=a_data["status"],
            distance_km=a_data["dist"],
            eta_minutes=a_data["eta"],
        )
        db.add(alloc)

    # 6. Alerts
    alerts_data = [
        {
            "zone": "ZONE_A",
            "title": "Critical Medical Shortage",
            "message": "Zone A trauma centers report zero reserves of surgical sutures and IV plasma. Urgent replenishment required.",
            "level": "CRITICAL",
        },
        {
            "zone": "ZONE_B",
            "title": "New Disaster Report Received",
            "message": "Citizen reports structural collapse of industrial complex in Zone B with ~15 workers trapped.",
            "level": "CRITICAL",
        },
        {
            "zone": "ZONE_A",
            "title": "Resource Delay Detected",
            "message": "Convoy NDRU-04 slowed due to NH-24 flash flood waterlogging. ETA extended by +15 min.",
            "level": "WARNING",
        },
        {
            "zone": "ZONE_C",
            "title": "Potential Duplicate Allocation",
            "message": "Both NGO Alpha and NGO Beta dispatched food convoys to Sector 9. Coordination suggested.",
            "level": "INFO",
        },
    ]

    for al_data in alerts_data:
        zn = zone_objs[al_data["zone"]]
        alert = Alert(
            zone_id=zn.id,
            title=al_data["title"],
            message=al_data["message"],
            alert_level=al_data["level"],
            is_active=True,
        )
        db.add(alert)

    # 7. Initial Reports
    reports_data = [
        {
            "zone": "ZONE_A",
            "type": "Flood",
            "desc": "Water levels reached 6 feet along riverbanks. Over 30 families on rooftops awaiting evacuation boats.",
            "affected": 45,
            "injured": 4,
            "missing": 2,
            "lat": 28.6145,
            "lng": 77.2085,
            "status": "VERIFIED",
        },
        {
            "zone": "ZONE_B",
            "type": "Earthquake",
            "desc": "Industrial building facade collapsed onto access road. Medical supplies needed immediately.",
            "affected": 30,
            "injured": 8,
            "missing": 1,
            "lat": 28.5360,
            "lng": 77.3915,
            "status": "VERIFIED",
        },
    ]

    for r_data in reports_data:
        zn = zone_objs[r_data["zone"]]
        report = Report(
            zone_id=zn.id,
            reporter_id=commander.id,
            disaster_type=r_data["type"],
            description=r_data["desc"],
            people_affected=r_data["affected"],
            injured_people=r_data["injured"],
            missing_people=r_data["missing"],
            latitude=r_data["lat"],
            longitude=r_data["lng"],
            status=r_data["status"],
        )
        db.add(report)

    # 8. Audit Logs
    now = datetime.utcnow()
    logs_data = [
        {
            "event": "ZONE_INITIALIZED",
            "desc": "5 High-risk Disaster Zones loaded into Command Operations Center.",
            "status": "SUCCESS",
            "ts": now - timedelta(minutes=15),
            "zone": "ZONE_A",
        },
        {
            "event": "REPORT_RECEIVED",
            "desc": "High priority flood emergency report verified in Zone A riverfront.",
            "status": "SUCCESS",
            "ts": now - timedelta(minutes=12),
            "zone": "ZONE_A",
        },
        {
            "event": "RESOURCE_ALLOCATED",
            "desc": "Urban Search & Rescue Team 02 dispatched to Zone A.",
            "status": "SUCCESS",
            "ts": now - timedelta(minutes=9),
            "zone": "ZONE_A",
        },
        {
            "event": "ETA_UPDATED",
            "desc": "Rescue Team 02 route computed. Estimated time of arrival: 8 minutes.",
            "status": "SUCCESS",
            "ts": now - timedelta(minutes=6),
            "zone": "ZONE_A",
        },
        {
            "event": "ALERT_CREATED",
            "desc": "Critical Medical Shortage alert triggered for Zone A by AI monitoring agent.",
            "status": "WARNING",
            "ts": now - timedelta(minutes=3),
            "zone": "ZONE_A",
        },
    ]

    for l_data in logs_data:
        zn = zone_objs[l_data["zone"]]
        log = AuditLog(
            user_id=commander.id,
            agency_id=agency_objs["Government Emergency Services"].id,
            zone_id=zn.id,
            event_type=l_data["event"],
            description=l_data["desc"],
            status=l_data["status"],
            timestamp=l_data["ts"],
        )
        db.add(log)

    db.commit()
    logger.info("Database seeding complete!")
