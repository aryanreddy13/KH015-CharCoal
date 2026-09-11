import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import { useWebSocket } from './useWebSocket';
import { Zone, Resource, Allocation, Need, Alert, AuditLog, DashboardKPI } from '../types';

export function useDashboardData() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [needs, setNeeds] = useState<Need[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [kpi, setKpi] = useState<DashboardKPI>({
    active_zones_count: 5,
    critical_zones_count: 2,
    available_resources_count: 6,
    active_allocations_count: 4,
    total_people_affected: 930,
  });
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { isConnected, registerListener } = useWebSocket();

  const loadAllData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [zonesData, resData, allocData, needsData, alertsData, logsData, kpiData] = await Promise.all([
        apiService.getZones(),
        apiService.getResources(),
        apiService.getAllocations(),
        apiService.getNeeds(),
        apiService.getAlerts(),
        apiService.getAuditLogs(30),
        apiService.getSummary(),
      ]);

      setZones(zonesData);
      setResources(resData);
      setAllocations(allocData);
      setNeeds(needsData);
      setAlerts(alertsData);
      setAuditLogs(logsData);
      setKpi(kpiData);

      if (!selectedZoneId && zonesData.length > 0) {
        setSelectedZoneId(zonesData[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message || 'Failed to connect to backend command server');
    } finally {
      setLoading(false);
    }
  }, [selectedZoneId]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // Handle WebSocket Event Subscriptions
  useEffect(() => {
    // 1. Zone Updated
    const unZone = registerListener('ZONE_UPDATED', (msg) => {
      setZones((prev) =>
        prev.map((z) => {
          if (z.id === msg.data.zone_id) {
            return {
              ...z,
              overall_severity: msg.data.severity ?? z.overall_severity,
              affected_people: msg.data.affected_people ?? z.affected_people,
              status: msg.data.status ?? z.status,
            };
          }
          return z;
        })
      );
      // Re-fetch KPI metrics
      apiService.getSummary().then(setKpi).catch(console.error);
    });

    // 2. Resource Updated
    const unRes = registerListener('RESOURCE_UPDATED', (msg) => {
      setResources((prev) =>
        prev.map((r) => (r.id === msg.data.resource_id ? { ...r, status: msg.data.status } : r))
      );
      apiService.getSummary().then(setKpi).catch(console.error);
    });

    // 3. Allocation Updated / ETA Updated
    const unAlloc = registerListener('ALLOCATION_UPDATED', (msg) => {
      setAllocations((prev) =>
        prev.map((a) =>
          a.id === msg.data.allocation_id
            ? { ...a, status: msg.data.status ?? a.status, eta_minutes: msg.data.eta_minutes ?? a.eta_minutes }
            : a
        )
      );
    });

    const unEta = registerListener('ETA_UPDATED', (msg) => {
      setAllocations((prev) =>
        prev.map((a) =>
          a.id === msg.data.allocation_id ? { ...a, eta_minutes: msg.data.new_eta } : a
        )
      );
    });

    // 4. Alert Created
    const unAlert = registerListener('ALERT_CREATED', (msg) => {
      setAlerts((prev) => [
        {
          id: msg.data.id || String(Date.now()),
          zone_id: msg.data.zone_id,
          title: msg.data.title,
          message: msg.data.message,
          alert_level: msg.data.alert_level || 'CRITICAL',
          is_active: true,
          created_at: new Date().toISOString(),
        },
        ...prev,
      ]);
    });

    // 4b. SOS Beacon Activated
    const unSos = registerListener('SOS_ACTIVATED', (msg) => {
      setAlerts((prev) => [
        {
          id: `sos-${msg.data.id || Date.now()}`,
          zone_id: msg.data.zone_id,
          title: `🚨 SOS ACTIVATED - ${msg.data.zone_name || 'Emergency Zone'}`,
          message: `Reporter: ${msg.data.reporter_name || 'Anonymous'} | GPS: ${msg.data.latitude?.toFixed?.(4) ?? msg.data.latitude}, ${msg.data.longitude?.toFixed?.(4) ?? msg.data.longitude} (±${msg.data.accuracy || 10}m) | Status: RESPONSE REQUIRED`,
          alert_level: 'CRITICAL',
          is_active: true,
          created_at: msg.data.created_at || new Date().toISOString(),
        },
        ...prev.filter((a) => !a.title?.includes(msg.data.incident_id || '')),
      ]);
      apiService.getSummary().then(setKpi).catch(console.error);
    });

    // 5. Audit Log Created
    const unLog = registerListener('AUDIT_LOG_CREATED', (msg) => {
      setAuditLogs((prev) => [
        {
          id: msg.data.id || String(Date.now()),
          event_type: msg.data.event_type,
          description: msg.data.description,
          status: msg.data.status || 'SUCCESS',
          timestamp: msg.data.timestamp || new Date().toISOString(),
        },
        ...prev.slice(0, 49),
      ]);
    });

    // 6. Simulation Trigger
    const unSim = registerListener('SIMULATION_EVENT', () => {
      loadAllData();
    });

    return () => {
      unZone();
      unRes();
      unAlloc();
      unEta();
      unAlert();
      unSos();
      unLog();
      unSim();
    };
  }, [registerListener, loadAllData]);

  const selectedZone = zones.find((z) => z.id === selectedZoneId) || zones[0] || null;

  return {
    zones,
    resources,
    allocations,
    needs,
    alerts,
    auditLogs,
    kpi,
    selectedZone,
    selectedZoneId,
    setSelectedZoneId,
    loading,
    error,
    isConnected,
    refresh: loadAllData,
  };
}
