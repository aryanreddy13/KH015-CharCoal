import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    JSON,
)
from sqlalchemy.orm import relationship
from app.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(50), default="OPERATOR")  # COMMANDER, OPERATOR, FIELD_AGENT, CITIZEN
    agency_id = Column(String(36), ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    agency = relationship("Agency", back_populates="users")
    reports = relationship("Report", back_populates="reporter")
    audit_logs = relationship("AuditLog", back_populates="user")


class Agency(Base):
    __tablename__ = "agencies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # FIRE_RESCUE, MEDICAL, NGO, GOVERNMENT, POLICE
    contact_number = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, STANDBY, DEPLOYED
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="agency")
    resources = relationship("Resource", back_populates="agency")
    audit_logs = relationship("AuditLog", back_populates="agency")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    disaster_type = Column(String(100), nullable=False)  # Flood, Earthquake, Cyclone, Fire, Landslide
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    overall_severity = Column(Float, nullable=False, default=5.0)  # 0.0 to 10.0
    affected_people = Column(Integer, nullable=False, default=0)
    status = Column(String(50), default="Critical")  # Critical, High, Moderate, Low, Resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reports = relationship("Report", back_populates="zone", cascade="all, delete-orphan")
    needs = relationship("Need", back_populates="zone", cascade="all, delete-orphan")
    allocations = relationship("Allocation", back_populates="zone", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="zone", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="zone")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    zone_id = Column(String(36), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    reporter_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    disaster_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    people_affected = Column(Integer, default=1)
    injured_people = Column(Integer, default=0)
    missing_people = Column(Integer, default=0)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    photo_url = Column(String(500), nullable=True)
    status = Column(String(50), default="PENDING REVIEW")  # PENDING REVIEW, VERIFIED, ACTIONED, REJECTED
    assessment_json = Column(JSON, nullable=True)
    assessment_version = Column(String(50), nullable=True)
    assessment_status = Column(String(50), nullable=True)
    priority_assessment_json = Column(JSON, nullable=True)
    priority_score = Column(Float, nullable=True)
    priority_level = Column(String(50), nullable=True)
    priority_scoring_version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    zone = relationship("Zone", back_populates="reports")
    reporter = relationship("User", back_populates="reports")
    updates = relationship("ReportUpdate", back_populates="report", cascade="all, delete-orphan")


class ReportUpdate(Base):
    __tablename__ = "report_updates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    status_change = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="updates")


class Need(Base):
    __tablename__ = "needs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    zone_id = Column(String(36), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    resource_type = Column(String(100), nullable=False)  # Rescue, Medical, Food, Water, Shelter
    quantity_required = Column(Integer, nullable=False, default=1)
    quantity_fulfilled = Column(Integer, nullable=False, default=0)
    severity = Column(Float, nullable=False, default=5.0)  # 0.0 to 10.0
    priority_score = Column(Float, nullable=False, default=5.0)
    status = Column(String(50), default="CRITICAL")  # CRITICAL, IN_PROGRESS, FULFILLED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    zone = relationship("Zone", back_populates="needs")
    allocations = relationship("Allocation", back_populates="need")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agency_id = Column(String(36), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    resource_type = Column(String(100), nullable=False)  # FOOD, WATER, SHELTER, MEDICINE, RESCUE, AMBULANCE
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)  # legacy total quantity alias
    total_quantity = Column(Integer, nullable=False, default=1)
    available_quantity = Column(Integer, nullable=False, default=1)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    allocated_quantity = Column(Integer, nullable=False, default=0)
    unit = Column(String(50), default="Units")  # Kits, Liters, Tents, Ambulances, Units
    location = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=False, default=28.6139)
    longitude = Column(Float, nullable=False, default=77.2090)
    status = Column(String(50), default="AVAILABLE")  # AVAILABLE, ALLOCATED, EN_ROUTE, DELIVERED, DEPLETED, MAINTENANCE
    capacity = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agency = relationship("Agency", back_populates="resources")
    allocations = relationship("Allocation", back_populates="resource")
    resource_allocations = relationship("ResourceAllocation", back_populates="resource")
    locations = relationship("ResourceLocation", back_populates="resource", cascade="all, delete-orphan")


class ResourceLocation(Base):
    __tablename__ = "resource_locations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resource_id = Column(String(36), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    heading = Column(Float, nullable=True, default=0.0)
    speed_kmh = Column(Float, nullable=True, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    resource = relationship("Resource", back_populates="locations")


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resource_id = Column(String(36), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    zone_id = Column(String(36), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    need_id = Column(String(36), ForeignKey("needs.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    status = Column(String(50), default="EN_ROUTE")  # ALLOCATED, EN_ROUTE, DELIVERED, CANCELLED, DELAYED
    distance_km = Column(Float, nullable=True, default=0.0)
    eta_minutes = Column(Integer, nullable=True, default=15)
    allocated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resource = relationship("Resource", back_populates="allocations")
    zone = relationship("Zone", back_populates="allocations")
    need = relationship("Need", back_populates="allocations")


class ResourceAllocation(Base):
    __tablename__ = "resource_allocations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(50), nullable=False, index=True)  # SOS-XXXX or incident identifier
    sos_id = Column(String(36), ForeignKey("sos_events.id", ondelete="SET NULL"), nullable=True)
    resource_id = Column(String(36), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    provider_agency_id = Column(String(36), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    resource_type = Column(String(100), nullable=False)  # FOOD, WATER, SHELTER, MEDICINE, RESCUE, AMBULANCE
    requested_quantity = Column(Integer, nullable=False, default=0)
    recommended_quantity = Column(Integer, nullable=False, default=0)
    allocated_quantity = Column(Integer, nullable=False, default=0)
    status = Column(String(50), default="ALLOCATED")  # REQUESTED, RECOMMENDED, ALLOCATED, PARTIALLY_ALLOCATED, DISPATCHED, IN_TRANSIT, DELIVERED, CANCELLED, UNAVAILABLE
    allocated_by = Column(String(255), default="AI Coordination Agent")
    allocated_at = Column(DateTime, default=datetime.utcnow)
    dispatched_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resource = relationship("Resource", back_populates="resource_allocations")
    provider_agency = relationship("Agency")
    sos_event = relationship("SOSEvent", back_populates="resource_allocations")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    zone_id = Column(String(36), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    alert_level = Column(String(50), default="CRITICAL")  # CRITICAL, WARNING, INFO
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    zone = relationship("Zone", back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    agency_id = Column(String(36), ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True)
    zone_id = Column(String(36), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False)  # REPORT_RECEIVED, RESOURCE_ALLOCATED, ETA_UPDATED, ZONE_UPDATED, ALERT_CREATED, SIMULATION_TRIGGERED
    description = Column(Text, nullable=False)
    status = Column(String(50), default="SUCCESS")  # SUCCESS, WARNING, FAILURE
    metadata_json = Column(Text, nullable=True)  # JSON string of contextual details
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
    agency = relationship("Agency", back_populates="audit_logs")
    zone = relationship("Zone", back_populates="audit_logs")


class SOSEvent(Base):
    __tablename__ = "sos_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(50), nullable=True, index=True)
    reporter_name = Column(String(255), nullable=True)
    contact = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True, default=10.0)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, RESPONDED, RESOLVED
    provider_status = Column(String(50), default="NEW")  # NEW, ACCEPTED, DISPATCHED, EN_ROUTE, ARRIVED, RESOLVED
    description = Column(Text, nullable=True)
    disaster_type = Column(String(100), default="Flood")
    severity = Column(Float, default=9.5)
    people_affected = Column(Integer, default=1)
    injured_people = Column(Integer, default=0)
    missing_people = Column(Integer, default=0)
    
    # Granular resource requirements
    food_required = Column(Boolean, default=False)
    food_quantity = Column(Integer, nullable=True)
    water_required = Column(Boolean, default=False)
    water_quantity = Column(Integer, nullable=True)
    shelter_required = Column(Boolean, default=False)
    shelter_quantity = Column(Integer, nullable=True)
    medicine_required = Column(Boolean, default=False)
    medicine_quantity = Column(Integer, nullable=True)
    rescue_required = Column(Boolean, default=False)
    rescue_units_required = Column(Integer, nullable=True)
    ambulance_required = Column(Boolean, default=False)
    ambulances_required = Column(Integer, nullable=True)

    required_resources_json = Column(Text, nullable=True)  # JSON string: ["Rescue", "Medical"]
    notified_agencies_json = Column(Text, nullable=True)   # JSON string of routed agencies
    photo_url = Column(String(500), nullable=True)
    distance_km = Column(Float, nullable=True, default=4.8)
    eta_minutes = Column(Integer, nullable=True, default=11)
    assigned_agency_id = Column(String(36), ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True)
    assigned_resource_id = Column(String(36), ForeignKey("resources.id", ondelete="SET NULL"), nullable=True)
    resend_status = Column(String(50), default="NOT_SENT")  # SENT, FAILED, DEMO
    pagerduty_status = Column(String(50), default="NOT_SENT")  # SENT, FAILED, DEMO
    assessment_json = Column(JSON, nullable=True)
    assessment_version = Column(String(50), nullable=True)
    assessment_status = Column(String(50), nullable=True)
    priority_assessment_json = Column(JSON, nullable=True)
    priority_score = Column(Float, nullable=True)
    priority_level = Column(String(50), nullable=True)
    priority_scoring_version = Column(String(50), nullable=True)
    zone_id = Column(String(36), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    zone = relationship("Zone")
    assigned_agency = relationship("Agency", foreign_keys=[assigned_agency_id])
    assigned_resource = relationship("Resource", foreign_keys=[assigned_resource_id])
    resource_allocations = relationship("ResourceAllocation", back_populates="sos_event", cascade="all, delete-orphan")
