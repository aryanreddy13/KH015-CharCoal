import { Zone, Resource, Allocation, Need, Alert, AuditLog, Report, DashboardKPI, Agency } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Trans-Type': 'application/json',
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => 'Network response error');
    throw new Error(`API error (${res.status}): ${errorText}`);
  }

  return res.json();
}

export const apiService = {
  // Health & Summary
  getHealth: () => fetchJson<{ status: string; database_connected: boolean }>('/health'),
  getSummary: () => fetchJson<DashboardKPI>('/summary'),

  // Zones
  getZones: () => fetchJson<Zone[]>('/zones'),
  getZoneById: (id: string) => fetchJson<Zone>(`/zones/${id}`),

  // Resources & Needs
  getResources: () => fetchJson<Resource[]>('/resources'),
  getResourceById: (id: string) => fetchJson<Resource>(`/resources/${id}`),
  getNeeds: () => fetchJson<Need[]>('/needs'),
  getAllocations: () => fetchJson<Allocation[]>('/allocations'),
  getAgencies: () => fetchJson<Agency[]>('/agencies'),

  // Alerts & Audit
  getAlerts: () => fetchJson<Alert[]>('/alerts'),
  createAlert: (alertData: {
    title: string;
    message: string;
    alert_level?: string;
    zone_id?: string;
    is_active?: boolean;
  }) =>
    fetchJson<Alert>('/alerts', {
      method: 'POST',
      body: JSON.stringify(alertData),
    }),
  getAuditLogs: (limit = 50) => fetchJson<AuditLog[]>(`/audit-logs?limit=${limit}`),

  // Reports
  getReports: (limit = 100) => fetchJson<Report[]>(`/reports?limit=${limit}`),
  createReport: (reportData: {
    disaster_type: string;
    description: string;
    people_affected: number;
    injured_people: number;
    missing_people: number;
    latitude: number;
    longitude: number;
    photo_url?: string;
    zone_id?: string;
  }) =>
    fetchJson<Report>('/reports', {
      method: 'POST',
      body: JSON.stringify(reportData),
    }),

  // Simulation Triggers
  startSimulation: () =>
    fetchJson<{ success: boolean; message: string; details: any }>('/simulation/start', {
      method: 'POST',
    }),
  injectEmergency: (zoneId?: string) =>
    fetchJson<{ success: boolean; message: string; details: any }>('/simulation/emergency', {
      method: 'POST',
      body: JSON.stringify({ zone_id: zoneId }),
    }),
  simulateRoadBlock: () =>
    fetchJson<{ success: boolean; message: string; details: any }>('/simulation/road-block', {
      method: 'POST',
    }),

  // Emergency Service Provider Operations Console
  getProviderAgencies: () => fetchJson<Agency[]>('/provider/agencies'),
  getProviderKPIs: (agencyType?: string, agencyId?: string) => {
    const params = new URLSearchParams();
    if (agencyType) params.append('agency_type', agencyType);
    if (agencyId) params.append('agency_id', agencyId);
    return fetchJson<any>(`/provider/kpis?${params.toString()}`);
  },
  getProviderIncidents: (agencyType?: string, agencyId?: string, statusFilter?: string) => {
    const params = new URLSearchParams();
    if (agencyType) params.append('agency_type', agencyType);
    if (agencyId) params.append('agency_id', agencyId);
    if (statusFilter) params.append('status_filter', statusFilter);
    return fetchJson<any[]>(`/provider/incidents?${params.toString()}`);
  },
  getProviderIncidentDetail: (incidentId: string) =>
    fetchJson<any>(`/provider/incidents/${incidentId}`),

  // Provider Lifecycle Actions
  acceptIncident: (incidentId: string, data?: { agency_id?: string; notes?: string }) =>
    fetchJson<any>(`/provider/incidents/${incidentId}/accept`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),
  dispatchIncident: (incidentId: string, data?: { agency_id?: string; resource_id?: string; notes?: string }) =>
    fetchJson<any>(`/provider/incidents/${incidentId}/dispatch`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),
  enRouteIncident: (incidentId: string, data?: { notes?: string }) =>
    fetchJson<any>(`/provider/incidents/${incidentId}/en-route`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),
  arrivedIncident: (incidentId: string, data?: { notes?: string }) =>
    fetchJson<any>(`/provider/incidents/${incidentId}/arrived`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),
  resolveIncident: (incidentId: string, data?: { notes?: string }) =>
    fetchJson<any>(`/provider/incidents/${incidentId}/resolve`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),

  // Citizen SOS Trigger
  triggerSOS: (sosData: any) =>
    fetchJson<any>('/sos', {
      method: 'POST',
      body: JSON.stringify(sosData),
    }),

  // Resource Allotment & Inventory Management
  getResourceAllocations: (incidentId?: string, agencyType?: string, statusFilter?: string) => {
    const params = new URLSearchParams();
    if (incidentId) params.append('incident_id', incidentId);
    if (agencyType) params.append('agency_type', agencyType);
    if (statusFilter) params.append('status', statusFilter);
    return fetchJson<any[]>(`/resource-allocations?${params.toString()}`);
  },
  getResourceInventory: (agencyType?: string) => {
    const params = new URLSearchParams();
    if (agencyType) params.append('agency_type', agencyType);
    return fetchJson<any[]>(`/resource-allocations/inventory?${params.toString()}`);
  },
  getResourceSummary: () => fetchJson<any>('/resource-allocations/summary'),
  approveResourceAllocation: (allocationId: string, actor = 'Provider Dispatcher') =>
    fetchJson<any>(`/resource-allocations/${allocationId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ actor }),
    }),
  dispatchResourceAllocation: (allocationId: string, data?: { actor?: string; notes?: string }) =>
    fetchJson<any>(`/resource-allocations/${allocationId}/dispatch`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),
  markResourceInTransit: (allocationId: string) =>
    fetchJson<any>(`/resource-allocations/${allocationId}/in-transit`, {
      method: 'POST',
    }),
  markResourceDelivered: (allocationId: string, data?: { actor?: string; notes?: string }) =>
    fetchJson<any>(`/resource-allocations/${allocationId}/deliver`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),
  cancelResourceAllocation: (allocationId: string, reason = 'Mission redirected or cancelled') =>
    fetchJson<any>(`/resource-allocations/${allocationId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
};

