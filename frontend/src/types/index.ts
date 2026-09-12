export interface Agency {
  id: string;
  name: string;
  type: 'FIRE_RESCUE' | 'MEDICAL' | 'NGO' | 'GOVERNMENT' | string;
  contact_number?: string;
  status: string;
  created_at: string;
}

export interface Need {
  id: string;
  zone_id: string;
  resource_type: string;
  quantity_required: number;
  quantity_fulfilled: number;
  severity: number;
  priority_score: number;
  status: 'CRITICAL' | 'IN_PROGRESS' | 'FULFILLED' | string;
  created_at: string;
  updated_at: string;
}

export interface Resource {
  id: string;
  agency_id: string;
  agency?: Agency;
  resource_type: string;
  name: string;
  quantity: number;
  latitude: number;
  longitude: number;
  status: 'AVAILABLE' | 'ALLOCATED' | 'EN_ROUTE' | 'DELIVERED' | 'DELAYED' | string;
  capacity?: string;
  created_at: string;
  updated_at: string;
}

export interface Allocation {
  id: string;
  resource_id: string;
  zone_id: string;
  need_id?: string;
  quantity: number;
  status: 'ALLOCATED' | 'EN_ROUTE' | 'DELIVERED' | 'DELAYED' | 'CANCELLED' | string;
  distance_km?: number;
  eta_minutes?: number;
  resource?: Resource;
  allocated_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  zone_id?: string;
  title: string;
  message: string;
  alert_level: 'CRITICAL' | 'WARNING' | 'INFO' | string;
  is_active: boolean;
  created_at: string;
}

export interface AuditLog {
  id: string;
  user_id?: string;
  agency_id?: string;
  zone_id?: string;
  event_type: string;
  description: string;
  status: 'SUCCESS' | 'WARNING' | 'FAILURE' | string;
  metadata_json?: string;
  timestamp: string;
}

export interface Report {
  id: string;
  zone_id?: string;
  reporter_id?: string;
  reporter_name?: string;
  reporter_phone?: string;
  location_text?: string;
  admin_notes?: string;
  disaster_type: string;
  description: string;
  people_affected: number;
  injured_people: number;
  missing_people: number;
  latitude: number;
  longitude: number;
  photo_url?: string;
  status: 'PENDING REVIEW' | 'VERIFIED' | 'ACCEPTED' | 'IN_PROGRESS' | 'ACTIONED' | 'RESOLVED' | 'DISMISSED' | 'REJECTED' | string;
  priority_score?: number;
  priority_level?: string;
  assessment?: any;
  priority_assessment?: any;
  created_at: string;
  updated_at?: string;
}

export interface Zone {
  id: string;
  name: string;
  disaster_type: string;
  latitude: number;
  longitude: number;
  overall_severity: number;
  affected_people: number;
  status: 'Critical' | 'High' | 'Moderate' | 'Low' | string;
  created_at: string;
  updated_at: string;
  needs: Need[];
  allocations?: Allocation[];
  reports?: Report[];
  alerts?: Alert[];
}

export interface DashboardKPI {
  active_zones_count: number;
  critical_zones_count: number;
  available_resources_count: number;
  active_allocations_count: number;
  total_people_affected: number;
}

export interface WebSocketMessage {
  event: string;
  data: any;
  timestamp: string;
}

export interface PriorityScoreComponents {
  affected_people: {
    value?: number | null;
    score: number;
    source: string;
  };
  disaster_type: {
    value?: string | null;
    score: number;
    source: string;
  };
  urgency_keywords: {
    matched: string[];
    score: number;
    source: string;
  };
}

export interface PriorityAssessment {
  incident_id?: string;
  zone_score: number;
  priority_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string;
  components: PriorityScoreComponents;
  fallbacks_used: string[];
  scoring_version: string;
  processed_at?: string;
}

export interface ProviderIncident {
  id: string;
  incident_id: string;
  disaster_type: string;
  zone_name: string;
  zone_id?: string;
  severity: number;
  priority_score?: number;
  priority_level?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string;
  priority_assessment?: PriorityAssessment;
  location_text: string;
  latitude: number;
  longitude: number;
  accuracy: number;
  people_affected: number;
  injured_people: number;
  missing_people: number;
  required_resources: string[];
  distance_km: number;
  eta_minutes: number;
  photo_url?: string;
  provider_status: 'NEW' | 'ACCEPTED' | 'DISPATCHED' | 'EN_ROUTE' | 'ARRIVED' | 'RESOLVED' | string;
  assigned_agency_id?: string;
  assigned_agency_name?: string;
  assigned_resource_id?: string;
  assigned_resource_name?: string;
  resend_status: string;
  pagerduty_status: string;
  created_at: string;
}

export interface ProviderKPI {
  agency_id?: string;
  agency_name?: string;
  agency_type?: string;
  active_incidents: number;
  critical_incidents: number;
  available_units: number;
  units_deployed: number;
  people_affected: number;
}

export interface ResourceAllocationItem {
  id: string;
  incident_id: string;
  sos_id?: string;
  resource_id: string;
  resource_name?: string;
  provider_agency_id: string;
  agency_name?: string;
  resource_type: string;
  requested_quantity: number;
  recommended_quantity: number;
  allocated_quantity: number;
  status: 'REQUESTED' | 'RECOMMENDED' | 'ALLOCATED' | 'PARTIALLY_ALLOCATED' | 'DISPATCHED' | 'IN_TRANSIT' | 'DELIVERED' | 'CANCELLED' | 'UNAVAILABLE' | string;
  allocated_by?: string;
  allocated_at: string;
  dispatched_at?: string;
  delivered_at?: string;
  cancelled_at?: string;
  notes?: string;
  unit?: string;
  created_at: string;
  updated_at: string;
}

export interface ResourceInventoryItem {
  id: string;
  agency_id: string;
  agency_type: string;
  agency_name: string;
  resource_type: string;
  resource_name: string;
  total_quantity: number;
  available_quantity: number;
  allocated_quantity: number;
  reserved_quantity: number;
  unit: string;
  status: string;
}

export interface ResourceSummaryStats {
  total_requested: number;
  total_allocated: number;
  total_dispatched: number;
  total_delivered: number;
  total_shortage: number;
  fulfillment_percentages: Record<string, number>;
  critical_shortages: Array<{
    incident_id: string;
    resource_type: string;
    requested: number;
    allocated: number;
    shortage: number;
    status: string;
    notes?: string;
  }>;
}

