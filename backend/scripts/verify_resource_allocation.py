import sys
import os
from datetime import datetime

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

from app.database.session import SessionLocal
from app.database.seeder import seed_database
from app.models.models import Resource, ResourceAllocation, SOSEvent, Agency
from app.services.resource_allocation_service import resource_allocation_service
from app.services.sos_service import sos_service
from app.schemas.schemas import SOSCreate

def run_verification():
    print("=========================================================")
    print("PS20 RESOURCE ALLOTMENT & INVENTORY VERIFICATION SUITE")
    print("=========================================================")
    db = SessionLocal()
    try:
        # 1. Seed and verify initial inventory
        print("\n--- STEP 1: Seeding database and verifying initial inventory ---")
        seed_database(db)

        ngo = db.query(Agency).filter(Agency.type == "NGO").first()
        fire = db.query(Agency).filter(Agency.type == "FIRE_RESCUE").first()
        med = db.query(Agency).filter(Agency.type == "MEDICAL").first()
        police = db.query(Agency).filter(Agency.type == "POLICE").first()

        assert ngo is not None, "NGO agency not found"
        assert fire is not None, "FIRE_RESCUE agency not found"
        assert med is not None, "MEDICAL agency not found"
        assert police is not None, "POLICE agency not found"

        from sqlalchemy import func

        # Check NGO resources
        food_res_init = db.query(Resource).join(Agency).filter(Agency.type == "NGO", func.upper(Resource.resource_type) == "FOOD").order_by(Resource.total_quantity.desc()).first()
        water_res_init = db.query(Resource).join(Agency).filter(Agency.type == "NGO", func.upper(Resource.resource_type) == "WATER").order_by(Resource.total_quantity.desc()).first()
        shelter_res_init = db.query(Resource).join(Agency).filter(Agency.type == "NGO", func.upper(Resource.resource_type) == "SHELTER").order_by(Resource.total_quantity.desc()).first()
        med_res_init = db.query(Resource).join(Agency).filter(Agency.type == "NGO", func.upper(Resource.resource_type) == "MEDICINE").order_by(Resource.total_quantity.desc()).first()
        fire_res_init = db.query(Resource).join(Agency).filter(Agency.type == "FIRE_RESCUE", func.upper(Resource.resource_type) == "RESCUE").order_by(Resource.total_quantity.desc()).first()
        amb_res_init = db.query(Resource).join(Agency).filter(Agency.type == "MEDICAL", func.upper(Resource.resource_type) == "AMBULANCE").order_by(Resource.total_quantity.desc()).first()

        assert food_res_init is not None, "NGO missing FOOD"
        assert water_res_init is not None, "NGO missing WATER"
        assert shelter_res_init is not None, "NGO missing SHELTER"
        assert med_res_init is not None, "NGO missing MEDICINE"
        assert fire_res_init is not None, "FIRE missing RESCUE"
        assert amb_res_init is not None, "MEDICAL missing AMBULANCE"

        print(f"NGO Food Available: {food_res_init.available_quantity} {food_res_init.unit}")
        print(f"NGO Water Available: {water_res_init.available_quantity} {water_res_init.unit}")
        print(f"NGO Shelter Available: {shelter_res_init.available_quantity} {shelter_res_init.unit}")
        print(f"NGO Medicine Available: {med_res_init.available_quantity} {med_res_init.unit}")
        print(f"FIRE Rescue Units Available: {fire_res_init.available_quantity} {fire_res_init.unit}")
        print(f"MEDICAL Ambulances Available: {amb_res_init.available_quantity} {amb_res_init.unit}")

        print("[PASS] Initial resource inventory and ownership verified successfully.")

        # 2. Test Requirement calculation formula
        print("\n--- STEP 2: Testing Triage Recommendation Formula ---")
        recs = resource_allocation_service.calculate_recommendations(
            disaster_type="Flood",
            severity=9.0,
            people_affected=50,
            injured_people=10,
            missing_people=5,
            explicit_requirements={
                "food_required": True,
                "food_quantity": 60,
                "water_required": True,
                "water_quantity": 120,
            }
        )
        assert "FOOD" in recs
        assert recs["FOOD"]["requested"] == 60
        assert recs["FOOD"]["recommended"] == 50  # 50 people * 1 kit

        assert "WATER" in recs
        assert recs["WATER"]["requested"] == 120
        assert recs["WATER"]["recommended"] == 100  # 50 people * 2 units

        assert "AMBULANCE" in recs
        assert recs["AMBULANCE"]["recommended"] == 5  # 10 injured / 2 per ambulance

        assert "RESCUE" in recs
        assert recs["RESCUE"]["recommended"] == 1  # 5 missing / 5 per team

        print(f"Calculated Recommendations: {recs}")
        print("[PASS] Formula calculation validated.")

        from sqlalchemy import func
        food_target_before = db.query(Resource).join(Agency).filter(Agency.type == "NGO", func.upper(Resource.resource_type) == "FOOD").order_by(Resource.available_quantity.desc()).first()
        amb_target_before = db.query(Resource).join(Agency).filter(Agency.type == "MEDICAL", func.upper(Resource.resource_type) == "AMBULANCE").order_by(Resource.available_quantity.desc()).first()
        initial_food_avail = food_target_before.available_quantity
        initial_amb_avail = amb_target_before.available_quantity
        target_food_id = food_target_before.id
        target_amb_id = amb_target_before.id

        sos_in = SOSCreate(
            reporter_name="Test Citizen Alok",
            latitude=28.6139,
            longitude=77.2090,
            disaster_type="Flood",
            severity=9.2,
            people_affected=20,
            injured_people=4,
            missing_people=2,
            food_required=True,
            food_quantity=25,
            water_required=True,
            water_quantity=50,
            shelter_required=False,
            medicine_required=True,
            medicine_quantity=4,
            rescue_required=True,
            rescue_units_required=1,
            ambulance_required=True,
            ambulances_required=2,
        )

        sos_event, alert, log = sos_service.create_sos(db, sos_in)
        print(f"Created SOS Event: {sos_event.incident_id} (ID: {sos_event.id})")

        # Query created allocations
        allocations = db.query(ResourceAllocation).filter(ResourceAllocation.sos_id == sos_event.id).all()
        assert len(allocations) > 0, "No resource allocations created for SOS event"
        print(f"Created {len(allocations)} allocations:")
        for a in allocations:
            print(f"  - {a.resource_type}: Req={a.requested_quantity}, Rec={a.recommended_quantity}, Alloc={a.allocated_quantity}, Status={a.status}")

        food_alloc_rec = [a for a in allocations if a.resource_type == "FOOD"][0]
        amb_alloc_rec = [a for a in allocations if a.resource_type == "AMBULANCE"][0]

        # Check inventory decremented on the allocated resources
        food_res_after = db.query(Resource).filter(Resource.id == food_alloc_rec.resource_id).first()
        amb_res_after = db.query(Resource).filter(Resource.id == amb_alloc_rec.resource_id).first()

        assert food_res_after.available_quantity == initial_food_avail - food_alloc_rec.allocated_quantity, f"Expected {initial_food_avail - food_alloc_rec.allocated_quantity}, got {food_res_after.available_quantity}"
        assert amb_res_after.available_quantity == initial_amb_avail - amb_alloc_rec.allocated_quantity, f"Expected {initial_amb_avail - amb_alloc_rec.allocated_quantity}, got {amb_res_after.available_quantity}"
        print(f"NGO Food Inventory decremented: {initial_food_avail} -> {food_res_after.available_quantity}")
        print(f"MEDICAL Ambulance Inventory decremented: {initial_amb_avail} -> {amb_res_after.available_quantity}")
        print("[PASS] Inventory decrement verified.")


        # 4. Test Lifecycle Transitions (Approve -> Dispatch -> In-Transit -> Deliver)
        print("\n--- STEP 4: Testing State Machine Transitions ---")
        amb_alloc = [a for a in allocations if a.resource_type == "AMBULANCE"][0]
        
        # Dispatch
        ok, msg, amb_alloc = resource_allocation_service.dispatch_allocation(db, amb_alloc.id, actor="Dispatcher Mike")
        assert ok, f"Dispatch failed: {msg}"
        assert amb_alloc.status == "DISPATCHED"
        assert amb_alloc.dispatched_at is not None
        print(f"Dispatched allocation: Status={amb_alloc.status}, Time={amb_alloc.dispatched_at}")

        # In Transit
        ok, msg, amb_alloc = resource_allocation_service.mark_in_transit(db, amb_alloc.id)
        assert ok, f"In-transit failed: {msg}"
        assert amb_alloc.status == "IN_TRANSIT"
        print(f"In-Transit allocation: Status={amb_alloc.status}")

        # Deliver
        ok, msg, amb_alloc = resource_allocation_service.mark_delivered(db, amb_alloc.id, actor="Paramedic Jane")
        assert ok, f"Deliver failed: {msg}"
        assert amb_alloc.status == "DELIVERED"
        assert amb_alloc.delivered_at is not None
        print(f"Delivered allocation: Status={amb_alloc.status}, Time={amb_alloc.delivered_at}")
        print("[PASS] Allocation lifecycle state machine passed.")

        # 5. Test Cancellation & Inventory Restoration
        print("\n--- STEP 5: Testing Cancellation & Stock Restoration ---")
        food_alloc = [a for a in allocations if a.resource_type == "FOOD"][0]
        food_res = db.query(Resource).filter(Resource.id == food_alloc.resource_id).first()
        food_avail_before_cancel = food_res.available_quantity

        ok, msg, food_alloc = resource_allocation_service.cancel_allocation(db, food_alloc.id, reason="False alarm in Sector 4")
        assert ok, f"Cancel failed: {msg}"
        assert food_alloc.status == "CANCELLED"
        assert food_alloc.cancelled_at is not None

        db.refresh(food_res)
        assert food_res.available_quantity == food_avail_before_cancel + food_alloc.allocated_quantity
        print(f"Restored {food_alloc.allocated_quantity} Food Kits: {food_avail_before_cancel} -> {food_res.available_quantity}")
        print("[PASS] Cancellation and stock replenishment verified.")

        # 6. Test Partial Allocation and Over-allocation Prevention
        print("\n--- STEP 6: Testing Stock Depletion & Shortage Handling ---")
        amb_res_heavy = db.query(Resource).join(Agency).filter(Agency.type == "MEDICAL", func.upper(Resource.resource_type) == "AMBULANCE").order_by(Resource.total_quantity.desc()).first()
        amb_res_heavy.available_quantity = 3
        amb_res_heavy.status = "AVAILABLE"
        db.commit()

        sos_heavy = SOSCreate(
            reporter_name="Disaster Heavy Event",
            latitude=28.6139,
            longitude=77.2090,
            disaster_type="Earthquake",
            severity=9.8,
            people_affected=100,
            injured_people=50,
            ambulance_required=True,
            ambulances_required=5,
        )

        heavy_sos, _, _ = sos_service.create_sos(db, sos_heavy)
        heavy_alloc = db.query(ResourceAllocation).filter(
            ResourceAllocation.sos_id == heavy_sos.id,
            ResourceAllocation.resource_type == "AMBULANCE"
        ).first()

        assert heavy_alloc is not None
        assert heavy_alloc.allocated_quantity == 3
        assert heavy_alloc.status == "PARTIALLY_ALLOCATED"
        assert "Shortage" in (heavy_alloc.notes or "")

        db.refresh(amb_res_heavy)
        assert amb_res_heavy.available_quantity == 0
        assert amb_res_heavy.status == "DEPLETED"
        print(f"Requested 5 Ambulances with 3 in stock:")
        print(f"  - Allocated: {heavy_alloc.allocated_quantity}")
        print(f"  - Status: {heavy_alloc.status}")
        print(f"  - Notes: {heavy_alloc.notes}")
        print(f"  - Inventory Remaining: {amb_res_heavy.available_quantity} (Status: {amb_res_heavy.status})")

        # Test subsequent request when stock is 0 -> UNAVAILABLE
        sos_empty = SOSCreate(
            reporter_name="Disaster Depleted Event",
            latitude=28.6139,
            longitude=77.2090,
            disaster_type="Earthquake",
            severity=9.8,
            people_affected=10,
            injured_people=4,
            ambulance_required=True,
            ambulances_required=2,
        )
        empty_sos, _, _ = sos_service.create_sos(db, sos_empty)
        empty_alloc = db.query(ResourceAllocation).filter(
            ResourceAllocation.sos_id == empty_sos.id,
            ResourceAllocation.resource_type == "AMBULANCE"
        ).first()
        assert empty_alloc.status == "UNAVAILABLE"
        assert empty_alloc.allocated_quantity == 0
        print(f"Subsequent request with 0 stock -> Status: {empty_alloc.status}")
        print("[PASS] Over-allocation prevention and shortage allotment verified.")

        # 7. Summary Stats Test
        print("\n--- STEP 7: Testing Summary Stats Endpoint Aggregations ---")
        summary = resource_allocation_service.get_summary_stats(db)
        print(f"Summary Stats: {summary}")
        assert summary["total_requested"] > 0
        assert summary["total_allocated"] > 0
        assert summary["total_shortage"] > 0
        assert len(summary["critical_shortages"]) > 0
        print("[PASS] Summary stats aggregations verified.")

        print("\n=========================================================")
        print(">>> ALL RESOURCE ALLOTMENT VERIFICATION TESTS PASSED SUCCESSFULLY! <<<")
        print("=========================================================")

    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
