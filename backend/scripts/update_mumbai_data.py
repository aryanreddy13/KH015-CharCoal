import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import SessionLocal
from app.models.models import Zone, Resource, Report
from app.database.seeder import seed_database, mumbai_zones_info, primary_inventory

def migrate_to_mumbai():
    db = SessionLocal()
    try:
        print("Migrating Zones to Mumbai Metropolitan Region...")
        existing_zones = db.query(Zone).all()
        for idx, zone in enumerate(existing_zones):
            if idx < len(mumbai_zones_info):
                info = mumbai_zones_info[idx]
                print(f"Updating zone {zone.id}: '{zone.name}' -> '{info['name']}' at ({info['lat']}, {info['lng']})")
                zone.name = info["name"]
                zone.disaster_type = info["disaster_type"]
                zone.latitude = info["lat"]
                zone.longitude = info["lng"]
                zone.overall_severity = info["overall_severity"]
                zone.affected_people = info["affected_people"]
                zone.status = info["status"]
        
        print("\nUpdating Resources to Mumbai Coordinates...")
        res_list = db.query(Resource).all()
        for res in res_list:
            # Map resources to appropriate Mumbai locations
            if "FOOD" in res.resource_type.upper():
                res.latitude = 19.0657
                res.longitude = 72.8780
                res.location = "Kurla Regional Food Depot"
            elif "WATER" in res.resource_type.upper():
                res.latitude = 19.0200
                res.longitude = 72.8600
                res.location = "Wadala Potable Water Depot"
            elif "SHELTER" in res.resource_type.upper():
                res.latitude = 19.1860
                res.longitude = 72.8485
                res.location = "Malad Relief Warehouse"
            elif "MEDIC" in res.resource_type.upper():
                res.latitude = 19.0020
                res.longitude = 72.8420
                res.location = "KEM Hospital Trauma Hub Parel"
            elif "AMBULANCE" in res.resource_type.upper():
                res.latitude = 19.0600
                res.longitude = 72.8650
                res.location = "BKC Emergency Ambulance Base"
            elif "RESCUE" in res.resource_type.upper():
                res.latitude = 18.9750
                res.longitude = 72.8250
                res.location = "Mumbai Fire Brigade HQ Byculla"
            else:
                res.latitude = 19.0760
                res.longitude = 72.8777
                res.location = "Central Mumbai Hub"
            print(f"Updated Resource: {res.name} ({res.resource_type}) -> ({res.latitude}, {res.longitude})")

        db.commit()
        print("\nRe-running seed_database...")
        seed_database(db)
        print("Successfully synchronized all zones and resources to Mumbai!")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_to_mumbai()
