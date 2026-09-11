import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Resource, ResourceAllocation, Agency, SOSEvent, AuditLog
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

# Configurable formula parameters
FOOD_KITS_PER_PERSON = 1
WATER_UNITS_PER_PERSON = 2
SHELTER_SPACES_PER_PERSON = 1
MEDICINE_KITS_PER_INJURED = 1
AMBULANCE_CAPACITY = 2  # 1 ambulance per 2 injured victims
RESCUE_TEAM_CAPACITY = 5  # 1 rescue unit per 5 trapped/missing victims

AGENCY_RESOURCE_OWNERSHIP = {
    "FOOD": "NGO",
    "WATER": "NGO",
    "SHELTER": "NGO",
    "MEDICINE": "NGO",
    "RESCUE": "FIRE_RESCUE",
    "AMBULANCE": "MEDICAL",
}

class ResourceAllocationService:
    @staticmethod
    def calculate_recommendations(
        disaster_type: str,
        severity: float,
        people_affected: int = 1,
        injured_people: int = 0,
        missing_people: int = 0,
        explicit_requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculates recommended quantities based on configurable triage formulas
        and distinguishes between Requested, Recommended, and Agency.
        """
        if explicit_requirements is None:
            explicit_requirements = {}

        type_lower = (disaster_type or "").lower()
        affected = max(1, people_affected or 1)
        injured = max(0, injured_people or 0)
        missing = max(0, missing_people or 0)

        recommendations = {}

        # 1. FOOD
        food_req = explicit_requirements.get("food_required", False) or "food" in type_lower or affected >= 10
        if food_req:
            recommended_qty = affected * FOOD_KITS_PER_PERSON
            requested_qty = explicit_requirements.get("food_quantity") or recommended_qty
            recommendations["FOOD"] = {
                "agency_type": "NGO",
                "recommended": recommended_qty,
                "requested": requested_qty,
                "unit": "Kits",
            }

        # 2. WATER
        water_req = explicit_requirements.get("water_required", False) or "flood" in type_lower or affected >= 10
        if water_req:
            recommended_qty = affected * WATER_UNITS_PER_PERSON
            requested_qty = explicit_requirements.get("water_quantity") or recommended_qty
            recommendations["WATER"] = {
                "agency_type": "NGO",
                "recommended": recommended_qty,
                "requested": requested_qty,
                "unit": "Units",
            }

        # 3. SHELTER
        shelter_req = explicit_requirements.get("shelter_required", False) or "earthquake" in type_lower or "cyclone" in type_lower or affected >= 20
        if shelter_req:
            recommended_qty = affected * SHELTER_SPACES_PER_PERSON
            requested_qty = explicit_requirements.get("shelter_quantity") or recommended_qty
            recommendations["SHELTER"] = {
                "agency_type": "NGO",
                "recommended": recommended_qty,
                "requested": requested_qty,
                "unit": "Spaces",
            }

        # 4. MEDICINE
        med_req = explicit_requirements.get("medicine_required", False) or injured > 0 or severity >= 8.0
        if med_req:
            recommended_qty = max(1, injured * MEDICINE_KITS_PER_INJURED) if injured > 0 else (10 if severity >= 8.0 else 5)
            requested_qty = explicit_requirements.get("medicine_quantity") or recommended_qty
            recommendations["MEDICINE"] = {
                "agency_type": "NGO",
                "recommended": recommended_qty,
                "requested": requested_qty,
                "unit": "Kits",
            }

        # 5. RESCUE UNITS
        rescue_req = explicit_requirements.get("rescue_required", False) or "flood" in type_lower or "collapse" in type_lower or "fire" in type_lower or missing > 0 or severity >= 7.0
        if rescue_req:
            if missing > 0:
                recommended_qty = max(1, math.ceil(missing / RESCUE_TEAM_CAPACITY))
            elif severity >= 8.5:
                recommended_qty = 3
            elif severity >= 7.0:
                recommended_qty = 2
            else:
                recommended_qty = 1
            requested_qty = explicit_requirements.get("rescue_units_required") or recommended_qty
            recommendations["RESCUE"] = {
                "agency_type": "FIRE_RESCUE",
                "recommended": recommended_qty,
                "requested": requested_qty,
                "unit": "Units",
            }

        # 6. AMBULANCES
        amb_req = explicit_requirements.get("ambulance_required", False) or injured > 0 or severity >= 8.0
        if amb_req:
            recommended_qty = max(1, math.ceil(injured / AMBULANCE_CAPACITY)) if injured > 0 else 1
            requested_qty = explicit_requirements.get("ambulances_required") or recommended_qty
            recommendations["AMBULANCE"] = {
                "agency_type": "MEDICAL",
                "recommended": recommended_qty,
                "requested": requested_qty,
                "unit": "Ambulances",
            }

        return recommendations

    @classmethod
    def process_incident_allocations(
        cls,
        db: Session,
        sos: SOSEvent,
        explicit_requirements: Optional[Dict[str, Any]] = None,
    ) -> List[ResourceAllocation]:
        """
        Calculates requirements, executes inventory allocation with row locking,
        handles partial allocations & shortages, and saves ResourceAllocation records.
        """
        if explicit_requirements is None:
            explicit_requirements = {
                "food_required": sos.food_required,
                "food_quantity": sos.food_quantity,
                "water_required": sos.water_required,
                "water_quantity": sos.water_quantity,
                "shelter_required": sos.shelter_required,
                "shelter_quantity": sos.shelter_quantity,
                "medicine_required": sos.medicine_required,
                "medicine_quantity": sos.medicine_quantity,
                "rescue_required": sos.rescue_required,
                "rescue_units_required": sos.rescue_units_required,
                "ambulance_required": sos.ambulance_required,
                "ambulances_required": sos.ambulances_required,
            }

        recs = cls.calculate_recommendations(
            disaster_type=sos.disaster_type,
            severity=sos.severity,
            people_affected=sos.people_affected,
            injured_people=sos.injured_people,
            missing_people=sos.missing_people,
            explicit_requirements=explicit_requirements,
        )

        allocated_records: List[ResourceAllocation] = []

        # Agency cache
        agencies = {a.type: a for a in db.query(Agency).filter(Agency.status == "ACTIVE").all()}

        from sqlalchemy import func

        for res_type, r_info in recs.items():
            ag_type = r_info["agency_type"]

            # Lock resource row to prevent concurrent over-allocation
            try:
                resource = (
                    db.query(Resource)
                    .join(Agency, Resource.agency_id == Agency.id)
                    .filter(
                        Agency.type == ag_type,
                        func.upper(Resource.resource_type) == res_type.upper(),
                    )
                    .order_by(Resource.available_quantity.desc())
                    .with_for_update()
                    .first()
                )
            except Exception:
                # SQLite fallback without with_for_update support
                resource = (
                    db.query(Resource)
                    .join(Agency, Resource.agency_id == Agency.id)
                    .filter(
                        Agency.type == ag_type,
                        func.upper(Resource.resource_type) == res_type.upper(),
                    )
                    .order_by(Resource.available_quantity.desc())
                    .first()
                )

            if not resource:
                # Fallback: search by name or general match
                resource = (
                    db.query(Resource)
                    .join(Agency, Resource.agency_id == Agency.id)
                    .filter(
                        Agency.type == ag_type,
                        Resource.name.ilike(f"%{res_type}%")
                    )
                    .order_by(Resource.available_quantity.desc())
                    .first()
                )

            if not resource:
                continue

            agency = resource.agency

            req_qty = r_info["requested"]
            rec_qty = r_info["recommended"]
            avail_qty = resource.available_quantity if resource.available_quantity is not None else resource.quantity

            # Allocation calculation
            actual_allocated = min(req_qty, max(0, avail_qty))
            shortage = req_qty - actual_allocated

            if actual_allocated == req_qty and req_qty > 0:
                status = "ALLOCATED"
                notes = f"Fully allocated {actual_allocated} {r_info['unit']} from {agency.name}."
            elif actual_allocated > 0:
                status = "PARTIALLY_ALLOCATED"
                notes = f"Partially allocated {actual_allocated}/{req_qty} {r_info['unit']}. Shortage: {shortage} {r_info['unit']} unavailable in inventory."
            else:
                status = "UNAVAILABLE"
                notes = f"Shortage: {req_qty} {r_info['unit']} requested but 0 available in {agency.name} inventory."

            # Update inventory
            resource.available_quantity = max(0, avail_qty - actual_allocated)
            resource.allocated_quantity = (resource.allocated_quantity or 0) + actual_allocated
            if resource.available_quantity == 0:
                resource.status = "DEPLETED"

            # Create ResourceAllocation record
            alloc = ResourceAllocation(
                incident_id=sos.incident_id or f"SOS-{sos.id[:6].upper()}",
                sos_id=sos.id,
                resource_id=resource.id,
                provider_agency_id=agency.id,
                resource_type=res_type,
                requested_quantity=req_qty,
                recommended_quantity=rec_qty,
                allocated_quantity=actual_allocated,
                status=status,
                allocated_by="AI Coordination Agent",
                allocated_at=datetime.utcnow(),
                notes=notes,
            )
            db.add(alloc)
            db.flush()
            allocated_records.append(alloc)

            # Audit log
            audit_log = AuditLog(
                zone_id=sos.zone_id,
                agency_id=agency.id,
                event_type="RESOURCE_ALLOCATED" if status == "ALLOCATED" else ("RESOURCE_PARTIALLY_ALLOCATED" if status == "PARTIALLY_ALLOCATED" else "RESOURCE_SHORTAGE"),
                description=f"[{alloc.incident_id}] {res_type}: {notes}",
                status="SUCCESS" if status == "ALLOCATED" else "WARNING",
                timestamp=datetime.utcnow(),
            )
            db.add(audit_log)

        db.commit()

        # Real-time WebSocket broadcasting
        try:
            for rec in allocated_records:
                manager.broadcast_sync(
                    f"RESOURCE_{rec.status}",
                    {
                        "allocation_id": rec.id,
                        "incident_id": rec.incident_id,
                        "resource_type": rec.resource_type,
                        "requested": rec.requested_quantity,
                        "recommended": rec.recommended_quantity,
                        "allocated": rec.allocated_quantity,
                        "status": rec.status,
                        "notes": rec.notes,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
        except Exception as ws_err:
            logger.warning(f"WebSocket broadcast error for resource allocation: {ws_err}")

        return allocated_records

    @staticmethod
    def approve_allocation(db: Session, allocation_id: str, actor: str = "Provider Officer") -> Tuple[bool, str, Optional[ResourceAllocation]]:
        alloc = db.query(ResourceAllocation).filter(ResourceAllocation.id == allocation_id).first()
        if not alloc:
            return False, "Allocation not found", None
        alloc.status = "ALLOCATED"
        alloc.allocated_by = actor
        alloc.allocated_at = datetime.utcnow()
        alloc.notes = f"Approved by {actor} at {datetime.utcnow().strftime('%H:%M:%S UTC')}."
        db.commit()
        db.refresh(alloc)
        manager.broadcast_sync(
            "RESOURCE_ALLOCATED",
            {"allocation_id": alloc.id, "incident_id": alloc.incident_id, "status": alloc.status}
        )
        return True, "Allocation approved successfully", alloc

    @staticmethod
    def dispatch_allocation(db: Session, allocation_id: str, actor: str = "Provider Officer", notes: Optional[str] = None) -> Tuple[bool, str, Optional[ResourceAllocation]]:
        alloc = db.query(ResourceAllocation).filter(ResourceAllocation.id == allocation_id).first()
        if not alloc:
            return False, "Allocation not found", None
        if alloc.status in ("CANCELLED", "DELIVERED"):
            return False, f"Cannot dispatch allocation in '{alloc.status}' status", alloc
        alloc.status = "DISPATCHED"
        alloc.dispatched_at = datetime.utcnow()
        if notes:
            alloc.notes = f"{alloc.notes or ''} | Dispatch Note: {notes}"
        db.commit()
        db.refresh(alloc)
        manager.broadcast_sync(
            "RESOURCE_DISPATCHED",
            {"allocation_id": alloc.id, "incident_id": alloc.incident_id, "status": alloc.status}
        )
        return True, "Resource successfully dispatched", alloc

    @staticmethod
    def mark_in_transit(db: Session, allocation_id: str) -> Tuple[bool, str, Optional[ResourceAllocation]]:
        alloc = db.query(ResourceAllocation).filter(ResourceAllocation.id == allocation_id).first()
        if not alloc:
            return False, "Allocation not found", None
        alloc.status = "IN_TRANSIT"
        db.commit()
        db.refresh(alloc)
        manager.broadcast_sync(
            "RESOURCE_IN_TRANSIT",
            {"allocation_id": alloc.id, "incident_id": alloc.incident_id, "status": alloc.status}
        )
        return True, "Resource marked in-transit", alloc

    @staticmethod
    def mark_delivered(db: Session, allocation_id: str, actor: str = "Field Agent", notes: Optional[str] = None) -> Tuple[bool, str, Optional[ResourceAllocation]]:
        alloc = db.query(ResourceAllocation).filter(ResourceAllocation.id == allocation_id).first()
        if not alloc:
            return False, "Allocation not found", None
        alloc.status = "DELIVERED"
        alloc.delivered_at = datetime.utcnow()
        if notes:
            alloc.notes = f"{alloc.notes or ''} | Delivery Note: {notes}"
        db.commit()
        db.refresh(alloc)
        manager.broadcast_sync(
            "RESOURCE_DELIVERED",
            {"allocation_id": alloc.id, "incident_id": alloc.incident_id, "status": alloc.status}
        )
        return True, "Resource successfully delivered and deployed", alloc

    @staticmethod
    def cancel_allocation(db: Session, allocation_id: str, reason: str = "Cancelled by Authority") -> Tuple[bool, str, Optional[ResourceAllocation]]:
        alloc = db.query(ResourceAllocation).filter(ResourceAllocation.id == allocation_id).first()
        if not alloc:
            return False, "Allocation not found", None
        if alloc.status == "DELIVERED":
            return False, "Cannot cancel already delivered allocation", alloc

        # Release allocated quantity back to resource inventory
        if alloc.allocated_quantity > 0:
            resource = db.query(Resource).filter(Resource.id == alloc.resource_id).first()
            if resource:
                resource.available_quantity = (resource.available_quantity or 0) + alloc.allocated_quantity
                resource.allocated_quantity = max(0, (resource.allocated_quantity or 0) - alloc.allocated_quantity)
                if resource.status == "DEPLETED" and resource.available_quantity > 0:
                    resource.status = "AVAILABLE"

        alloc.status = "CANCELLED"
        alloc.cancelled_at = datetime.utcnow()
        alloc.notes = f"Cancelled: {reason}"
        db.commit()
        db.refresh(alloc)
        manager.broadcast_sync(
            "RESOURCE_CANCELLED",
            {"allocation_id": alloc.id, "incident_id": alloc.incident_id, "status": alloc.status}
        )
        return True, "Allocation cancelled and inventory restored", alloc

    @staticmethod
    def get_agency_inventory(db: Session, agency_type: Optional[str] = None) -> List[Dict[str, Any]]:
        query = db.query(Resource).join(Agency, Resource.agency_id == Agency.id)
        if agency_type:
            query = query.filter(Agency.type == agency_type)
        resources = query.all()

        results = []
        for r in resources:
            tot = r.total_quantity if r.total_quantity is not None else r.quantity
            avail = r.available_quantity if r.available_quantity is not None else tot
            alloc = r.allocated_quantity if r.allocated_quantity is not None else 0
            resv = r.reserved_quantity if r.reserved_quantity is not None else 0
            results.append({
                "id": r.id,
                "agency_id": r.agency_id,
                "agency_type": r.agency.type if r.agency else "UNKNOWN",
                "agency_name": r.agency.name if r.agency else "Unknown Agency",
                "resource_type": r.resource_type,
                "resource_name": r.name,
                "total_quantity": tot,
                "available_quantity": avail,
                "allocated_quantity": alloc,
                "reserved_quantity": resv,
                "unit": r.unit or "Units",
                "status": r.status,
            })
        return results

    @staticmethod
    def get_summary_stats(db: Session) -> Dict[str, Any]:
        allocations = db.query(ResourceAllocation).all()
        total_requested = sum(a.requested_quantity for a in allocations)
        total_allocated = sum(a.allocated_quantity for a in allocations)
        total_dispatched = sum(a.allocated_quantity for a in allocations if a.status in ("DISPATCHED", "IN_TRANSIT", "DELIVERED"))
        total_delivered = sum(a.allocated_quantity for a in allocations if a.status == "DELIVERED")
        total_shortage = sum(max(0, a.requested_quantity - a.allocated_quantity) for a in allocations)

        # Fulfillment by type
        by_type: Dict[str, Dict[str, int]] = {
            "FOOD": {"req": 0, "alloc": 0},
            "WATER": {"req": 0, "alloc": 0},
            "SHELTER": {"req": 0, "alloc": 0},
            "MEDICINE": {"req": 0, "alloc": 0},
            "RESCUE": {"req": 0, "alloc": 0},
            "AMBULANCE": {"req": 0, "alloc": 0},
        }

        critical_shortages = []
        for a in allocations:
            rt = a.resource_type.upper()
            if rt in by_type:
                by_type[rt]["req"] += a.requested_quantity
                by_type[rt]["alloc"] += a.allocated_quantity
            if a.status in ("PARTIALLY_ALLOCATED", "UNAVAILABLE"):
                critical_shortages.append({
                    "incident_id": a.incident_id,
                    "resource_type": a.resource_type,
                    "requested": a.requested_quantity,
                    "allocated": a.allocated_quantity,
                    "shortage": a.requested_quantity - a.allocated_quantity,
                    "status": a.status,
                    "notes": a.notes,
                })

        percentages = {}
        for k, v in by_type.items():
            if v["req"] > 0:
                percentages[k] = round((v["alloc"] / v["req"]) * 100, 1)
            else:
                percentages[k] = 100.0

        return {
            "total_requested": total_requested,
            "total_allocated": total_allocated,
            "total_dispatched": total_dispatched,
            "total_delivered": total_delivered,
            "total_shortage": total_shortage,
            "fulfillment_percentages": percentages,
            "critical_shortages": critical_shortages,
        }

resource_allocation_service = ResourceAllocationService()
