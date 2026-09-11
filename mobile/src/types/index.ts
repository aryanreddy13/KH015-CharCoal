export type DisasterType =
  | 'Flood'
  | 'Earthquake'
  | 'Cyclone'
  | 'Fire'
  | 'Landslide'
  | 'Other';

export type RequiredResource =
  | 'Rescue'
  | 'Medical'
  | 'Medicine'
  | 'Food'
  | 'Water'
  | 'Shelter';

export type SyncStatus = 'PENDING_SYNC' | 'SYNCING' | 'SENT' | 'FAILED';

export type ReportServerStatus =
  | 'PENDING REVIEW'
  | 'VERIFIED'
  | 'ACTIONED'
  | 'REJECTED'
  | 'RESOLVED';

export interface LocationData {
  latitude: number;
  longitude: number;
  accuracy: number | null;
  timestamp: number;
  isManualFallback?: boolean;
}

export type LocationLockState =
  | 'IDLE'
  | 'ACQUIRING'
  | 'LOCKED'
  | 'PERMISSION_DENIED'
  | 'UNAVAILABLE'
  | 'MANUAL';

export interface SOSPayload {
  reporter_name?: string;
  contact?: string;
  latitude: number;
  longitude: number;
  accuracy?: number;
  description?: string;
  disaster_type?: string;
  people_affected?: number;
  injured_people?: number;
  missing_people?: number;
  photo_url?: string;
  required_resources?: string[];
  timestamp?: string;
}

export interface LocalSOSItem {
  local_id: string;
  created_at: string;
  sync_status: SyncStatus;
  payload: SOSPayload;
  incident_id?: string;
  server_id?: string;
  error_message?: string;
}

export interface ReportPayload {
  disaster_type: DisasterType;
  description: string;
  people_affected: number;
  injured_people: number;
  missing_people: number;
  latitude: number;
  longitude: number;
  required_resources?: string[];
  photo_url?: string;
  reporter_id?: string;
  status?: string;
}

export interface LocalReportItem {
  local_id: string;
  created_at: string;
  sync_status: SyncStatus;
  payload: ReportPayload;
  server_id?: string;
  server_status?: ReportServerStatus | string;
  photo_uri?: string;
  error_message?: string;
}

export interface EmergencyService {
  id: string;
  name: string;
  type: 'HOSPITAL' | 'POLICE' | 'FIRE_RESCUE' | 'NGO' | 'GOVERNMENT' | string;
  agency_type?: string;
  contact_number?: string;
  phone?: string;
  status: string;
  distance_meters?: number | null;
  distance_km?: number | null;
  distance_text?: string | null;
  eta_seconds?: number | null;
  eta_minutes?: number | null;
  eta_text?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  address?: string;
  maps_url?: string;
  source?: 'OPENSTREETMAP' | 'OSM_OSRM' | 'TOMTOM' | 'DATABASE' | string;
  is_registered_provider?: boolean;
  available_resources?: Array<{
    resource_id: string;
    resource_type: string;
    name: string;
    available_quantity: number;
    unit: string;
  }>;
}

export interface UserSettings {
  reporter_name: string;
  emergency_contact: string;
  custom_api_url?: string;
}
