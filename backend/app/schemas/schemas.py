from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field

# --- Base Schema ---
class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# --- Need & Assessment Agent Canonical Schemas ---
class FactualNumber(BaseModel):
    value: Optional[int] = Field(None, ge=0)
    source: str = "UNKNOWN"

class DisasterAssessment(BaseModel):
    type: Optional[str] = None
    source: str = "UNKNOWN"

class PeopleAssessment(BaseModel):
    affected: FactualNumber = Field(default_factory=lambda: FactualNumber(value=None, source="UNKNOWN"))
    injured: FactualNumber = Field(default_factory=lambda: FactualNumber(value=None, source="UNKNOWN"))
    trapped: FactualNumber = Field(default_factory=lambda: FactualNumber(value=None, source="UNKNOWN"))
    missing: FactualNumber = Field(default_factory=lambda: FactualNumber(value=None, source="UNKNOWN"))
    casualties: FactualNumber = Field(default_factory=lambda: FactualNumber(value=None, source="UNKNOWN"))

class ExplicitResourceRequest(BaseModel):
    resource_type: str
    quantity: Optional[int] = Field(None, ge=0)
    source: str = "USER_DESCRIPTION"

class ExtractionMetadata(BaseModel):
    agent: str = "NEED_ASSESSMENT"
    version: str = "1.0"
    source: str = "SYSTEM"
    prompt_version: str = "1.0"
    model: Optional[str] = None
    processed_at: Optional[str] = None

class IncidentAssessment(BaseModel):
    incident_id: Optional[str] = None
    input_mode: str = "REPORT"  # "REPORT" or "SOS"
    location: Dict[str, float]  # {"latitude": float, "longitude": float}
    disaster: DisasterAssessment
    people: PeopleAssessment
    needs: Dict[str, bool] = Field(
        default_factory=lambda: {
            "FOOD": False,
            "WATER": False,
            "SHELTER": False,
            "MEDICINE": False,
            "RESCUE": False,
            "AMBULANCE": False,
        }
    )
    explicit_requests: List[ExplicitResourceRequest] = []
    urgency_keywords: List[str] = []
    facts: List[str] = []
    extraction_metadata: ExtractionMetadata

# --- Priority & Severity Agent Canonical Schemas ---
class PeopleScoreComponent(BaseModel):
    value: Optional[int] = None
    score: float
    source: str

class DisasterScoreComponent(BaseModel):
    value: Optional[str] = None
    score: float
    source: str

class UrgencyScoreComponent(BaseModel):
    matched: List[str] = []
    score: float
    source: str = "NEED_ASSESSMENT"

class PriorityScoreComponents(BaseModel):
    affected_people: PeopleScoreComponent
    disaster_type: DisasterScoreComponent
    urgency_keywords: UrgencyScoreComponent

class PriorityAssessment(BaseModel):
    incident_id: Optional[str] = None
    zone_score: float
    priority_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    components: PriorityScoreComponents
    fallbacks_used: List[str] = []
    scoring_version: str = "1.0"
    processed_at: Optional[str] = None

class IncidentContext(BaseModel):
    incident_id: str
    input_mode: str
    location: Dict[str, float]
    assessment: IncidentAssessment
    priority: Optional[PriorityAssessment] = None
    external_enrichment: Optional[Dict[str, Any]] = None
    resource_requirements: Optional[Dict[str, Any]] = None
    allocation: Optional[Dict[str, Any]] = None

# --- Agency Schemas ---
class AgencyBase(BaseModel):
    name: str
    type: str
    contact_number: Optional[str] = None
    email: Optional[str] = None
    status: str = "ACTIVE"

class AgencyCreate(AgencyBase):
    pass

class AgencyResponse(AgencyBase, ORMModel):
    id: str
    created_at: datetime

# --- Need Schemas ---
class NeedBase(BaseModel):
    resource_type: str
    quantity_required: int
    quantity_fulfilled: int = 0
    severity: float
    priority_score: float
    status: str = "CRITICAL"

class NeedCreate(NeedBase):
    zone_id: str

class NeedResponse(NeedBase, ORMModel):
    id: str
    zone_id: str
    created_at: datetime
    updated_at: datetime

# --- Resource Schemas ---
class ResourceBase(BaseModel):
    name: str
    resource_type: str  # FOOD, WATER, SHELTER, MEDICINE, RESCUE, AMBULANCE
    quantity: int = 1
    total_quantity: int = 1
    available_quantity: int = 1
    reserved_quantity: int = 0
    allocated_quantity: int = 0
    unit: str = "Units"
    location: Optional[str] = None
    latitude: float = 28.6139
    longitude: float = 77.2090
    status: str = "AVAILABLE"
    capacity: Optional[str] = None

class ResourceCreate(ResourceBase):
    agency_id: str

class ResourceResponse(ResourceBase, ORMModel):
    id: str
    agency_id: str
    agency: Optional[AgencyResponse] = None
    created_at: datetime
    updated_at: datetime

# --- Resource Allocation Schemas ---
class ResourceAllocationBase(BaseModel):
    incident_id: str
    resource_id: str
    provider_agency_id: str
    resource_type: str
    requested_quantity: int = 0
    recommended_quantity: int = 0
    allocated_quantity: int = 0
    status: str = "ALLOCATED"  # REQUESTED, RECOMMENDED, ALLOCATED, PARTIALLY_ALLOCATED, DISPATCHED, IN_TRANSIT, DELIVERED, CANCELLED, UNAVAILABLE
    allocated_by: Optional[str] = "AI Coordination Agent"
    notes: Optional[str] = None

class ResourceAllocationCreate(ResourceAllocationBase):
    sos_id: Optional[str] = None

class ResourceAllocationResponse(ResourceAllocationBase, ORMModel):
    id: str
    sos_id: Optional[str] = None
    allocated_at: datetime
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    resource_name: Optional[str] = None
    agency_name: Optional[str] = None
    unit: Optional[str] = "Units"

class ResourceInventoryResponse(BaseModel):
    resource_type: str
    resource_name: str
    total_quantity: int
    available_quantity: int
    allocated_quantity: int
    reserved_quantity: int
    unit: str
    status: str

class ResourceSummaryStats(BaseModel):
    total_requested: int
    total_allocated: int
    total_dispatched: int
    total_delivered: int
    total_shortage: int
    fulfillment_percentages: Dict[str, float]
    critical_shortages: List[Dict[str, Any]] = []

# --- Allocation Schemas ---
class AllocationBase(BaseModel):
    quantity: int
    status: str = "EN_ROUTE"
    distance_km: Optional[float] = 0.0
    eta_minutes: Optional[int] = 15

class AllocationCreate(AllocationBase):
    resource_id: str
    zone_id: str
    need_id: Optional[str] = None

class AllocationResponse(AllocationBase, ORMModel):
    id: str
    resource_id: str
    zone_id: str
    need_id: Optional[str] = None
    resource: Optional[ResourceResponse] = None
    allocated_at: datetime
    updated_at: datetime

# --- Alert Schemas ---
class AlertBase(BaseModel):
    title: str
    message: str
    alert_level: str = "CRITICAL"
    is_active: bool = True

class AlertCreate(AlertBase):
    zone_id: Optional[str] = None

class AlertResponse(AlertBase, ORMModel):
    id: str
    zone_id: Optional[str] = None
    created_at: datetime

# --- Audit Log Schemas ---
class AuditLogBase(BaseModel):
    event_type: str
    description: str
    status: str = "SUCCESS"
    metadata_json: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    user_id: Optional[str] = None
    agency_id: Optional[str] = None
    zone_id: Optional[str] = None

class AuditLogResponse(AuditLogBase, ORMModel):
    id: str
    user_id: Optional[str] = None
    agency_id: Optional[str] = None
    zone_id: Optional[str] = None
    timestamp: datetime

# --- Report Schemas ---
class ReportBase(BaseModel):
    disaster_type: Optional[str] = None
    description: Optional[str] = None
    people_affected: Optional[int] = Field(None, ge=0)
    injured_people: Optional[int] = Field(None, ge=0)
    missing_people: Optional[int] = Field(None, ge=0)
    people_injured: Optional[int] = Field(None, ge=0)
    people_trapped: Optional[int] = Field(None, ge=0)
    people_missing: Optional[int] = Field(None, ge=0)
    casualties: Optional[int] = Field(None, ge=0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    photo_url: Optional[str] = None
    reporter_name: Optional[str] = "Citizen Reporter"
    reporter_phone: Optional[str] = None
    location_text: Optional[str] = None
    admin_notes: Optional[str] = None
    status: str = "PENDING REVIEW"
    input_mode: Optional[str] = "REPORT"

class ReportCreate(ReportBase):
    zone_id: Optional[str] = None
    reporter_id: Optional[str] = None
    required_resources: Optional[List[str]] = None

class ReportStatusUpdate(BaseModel):
    status: str  # PENDING REVIEW, VERIFIED, ACCEPTED, IN_PROGRESS, ACTIONED, RESOLVED, DISMISSED, REJECTED
    notes: Optional[str] = None
    actor: Optional[str] = "Command Administrator"
    assigned_agency_id: Optional[str] = None

class ReportActionRequest(BaseModel):
    notes: Optional[str] = None
    actor: Optional[str] = "Command Administrator"
    agency_id: Optional[str] = None
    resource_id: Optional[str] = None

class ReportResponse(ReportBase, ORMModel):
    id: str
    zone_id: Optional[str] = None
    reporter_id: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    location_text: Optional[str] = None
    admin_notes: Optional[str] = None
    assessment: Optional[IncidentAssessment] = None
    priority_assessment: Optional[PriorityAssessment] = None
    priority_level: Optional[str] = None
    priority_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

# --- Zone Schemas ---
class ZoneBase(BaseModel):
    name: str
    disaster_type: str
    latitude: float
    longitude: float
    overall_severity: float
    affected_people: int
    status: str = "Critical"

class ZoneCreate(ZoneBase):
    pass

class ZoneResponse(ZoneBase, ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime
    needs: List[NeedResponse] = []

class ZoneDetailResponse(ZoneResponse):
    allocations: List[AllocationResponse] = []
    reports: List[ReportResponse] = []
    alerts: List[AlertResponse] = []

# --- Dashboard Summary KPI Schemas ---
class DashboardKPISummary(BaseModel):
    active_zones_count: int
    critical_zones_count: int
    available_resources_count: int
    active_allocations_count: int
    total_people_affected: int

# --- WebSocket Message Schema ---
class WebSocketEvent(BaseModel):
    event: str
    data: Dict[str, Any]
    timestamp: str

# --- SOS Schemas ---
class SOSCreate(BaseModel):
    reporter_name: Optional[str] = "Anonymous Citizen"
    contact: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    accuracy: Optional[float] = 10.0
    description: Optional[str] = "EMERGENCY SOS TRIGGERED"
    disaster_type: Optional[str] = "Flood"
    severity: Optional[float] = 9.5
    people_affected: Optional[int] = Field(None, ge=0)
    injured_people: Optional[int] = Field(None, ge=0)
    missing_people: Optional[int] = Field(None, ge=0)
    people_injured: Optional[int] = Field(None, ge=0)
    people_trapped: Optional[int] = Field(None, ge=0)
    people_missing: Optional[int] = Field(None, ge=0)
    casualties: Optional[int] = Field(None, ge=0)
    input_mode: Optional[str] = "SOS"
    
    # Granular resource requirements
    food_required: Optional[bool] = False
    food_quantity: Optional[int] = None
    water_required: Optional[bool] = False
    water_quantity: Optional[int] = None
    shelter_required: Optional[bool] = False
    shelter_quantity: Optional[int] = None
    medicine_required: Optional[bool] = False
    medicine_quantity: Optional[int] = None
    rescue_required: Optional[bool] = False
    rescue_units_required: Optional[int] = None
    ambulance_required: Optional[bool] = False
    ambulances_required: Optional[int] = None

    photo_url: Optional[str] = None
    required_resources: Optional[List[str]] = ["Rescue", "Medical"]
    timestamp: Optional[str] = None

class SOSResponse(BaseModel):
    id: str
    incident_id: str
    status: str = "ACTIVATED"
    provider_status: Optional[str] = "NEW"
    message: str = "Emergency signal received"
    latitude: float
    longitude: float
    accuracy: Optional[float] = 10.0
    reporter_name: Optional[str] = None
    disaster_type: Optional[str] = "Flood"
    severity: Optional[float] = 9.5
    people_affected: Optional[int] = 1
    injured_people: Optional[int] = 0
    missing_people: Optional[int] = 0
    
    food_required: Optional[bool] = False
    food_quantity: Optional[int] = None
    water_required: Optional[bool] = False
    water_quantity: Optional[int] = None
    shelter_required: Optional[bool] = False
    shelter_quantity: Optional[int] = None
    medicine_required: Optional[bool] = False
    medicine_quantity: Optional[int] = None
    rescue_required: Optional[bool] = False
    rescue_units_required: Optional[int] = None
    ambulance_required: Optional[bool] = False
    ambulances_required: Optional[int] = None

    photo_url: Optional[str] = None
    distance_km: Optional[float] = 4.8
    eta_minutes: Optional[int] = 11
    required_resources: Optional[List[str]] = []
    notified_agencies: Optional[List[Dict[str, Any]]] = []
    resource_allocations: Optional[List[Dict[str, Any]]] = []
    assessment: Optional[IncidentAssessment] = None
    priority_assessment: Optional[PriorityAssessment] = None
    priority_level: Optional[str] = None
    priority_score: Optional[float] = None
    resend_status: Optional[str] = "NOT_SENT"
    pagerduty_status: Optional[str] = "NOT_SENT"
    created_at: datetime

# --- Provider Incident Schemas ---
class ProviderIncidentResponse(BaseModel):
    id: str
    incident_id: str
    disaster_type: str
    zone_name: str
    zone_id: Optional[str] = None
    severity: float
    priority_score: Optional[float] = None
    priority_level: Optional[str] = None
    priority_assessment: Optional[Dict[str, Any]] = None
    location_text: str
    latitude: float
    longitude: float
    accuracy: float
    people_affected: int
    injured_people: int
    missing_people: int
    required_resources: List[str]
    distance_km: float
    eta_minutes: int
    photo_url: Optional[str] = None
    provider_status: str  # NEW, ACCEPTED, DISPATCHED, EN_ROUTE, ARRIVED, RESOLVED
    assigned_agency_id: Optional[str] = None
    assigned_agency_name: Optional[str] = None
    assigned_resource_id: Optional[str] = None
    assigned_resource_name: Optional[str] = None
    resend_status: str
    pagerduty_status: str
    created_at: str

class ProviderKPIsResponse(BaseModel):
    agency_id: Optional[str] = None
    agency_name: Optional[str] = None
    agency_type: Optional[str] = None
    active_incidents: int
    critical_incidents: int
    available_units: int
    units_deployed: int
    people_affected: int

class ProviderActionRequest(BaseModel):
    agency_id: Optional[str] = None
    resource_id: Optional[str] = None
    notes: Optional[str] = None

class ProviderActionResponse(BaseModel):
    success: bool
    message: str
    incident_id: str
    new_status: str
    incident: ProviderIncidentResponse

# --- Emergency Services Schemas ---
class EmergencyServiceItem(BaseModel):
    id: str
    name: str
    type: str  # HOSPITAL, POLICE, FIRE_RESCUE, MEDICAL, NGO, GOVERNMENT
    agency_type: Optional[str] = None
    contact_number: Optional[str] = None
    phone: Optional[str] = None
    status: str = "ACTIVE"
    distance_meters: Optional[int] = None
    distance_km: Optional[float] = None
    distance_text: Optional[str] = None
    eta_seconds: Optional[int] = None
    eta_minutes: Optional[int] = None
    eta_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    maps_url: Optional[str] = None
    source: Optional[str] = "TOMTOM"
    is_registered_provider: Optional[bool] = False
    available_resources: Optional[List[Dict[str, Any]]] = None

class EmergencyServicesResponse(BaseModel):
    count: int
    services: List[EmergencyServiceItem]

# --- Simulation Schemas ---
class SimulationActionRequest(BaseModel):
    scenario: Optional[str] = "default"
    zone_id: Optional[str] = None
    severity_delta: Optional[float] = 1.0
    notes: Optional[str] = None

class SimulationActionResponse(BaseModel):
    success: bool
    message: str
    event_type: str
    details: Dict[str, Any] = {}

