import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import { useWebSocket } from './useWebSocket';
import { Zone, Resource, Allocation, Need, Alert, AuditLog, Report, DashboardKPI } from '../types';

export function useDashboardData() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [needs, setNeeds] = useState<Need[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
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
  const [incomingAlertToast, setIncomingAlertToast] = useState<{
    id: string;
    title: string;
    description: string;
    type: string;
    time: string;
  } | null>(null);

  const { isConnected, registerListener } = useWebSocket();

  const loadAllData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [zonesData, resData, allocData, needsData, alertsData, logsData, kpiData, reportsData] = await Promise.all([
        apiService.getZones().catch(() => []),
        apiService.getResources().catch(() => []),
        apiService.getAllocations().catch(() => []),
        apiService.getNeeds().catch(() => []),
        apiService.getAlerts().catch(() => []),
        apiService.getAuditLogs(30).catch(() => []),
        apiService.getSummary().catch(() => ({
          active_zones_count: 5,
          critical_zones_count: 2,
          available_resources_count: 6,
          active_allocations_count: 4,
          total_people_affected: 930,
        })),
        apiService.getReports(100).catch(() => []),
      ]);

      setZones(zonesData);
      setResources(resData);
      setAllocations(allocData);
      setNeeds(needsData);
      setAlerts(alertsData);
      setAuditLogs(logsData);
      setKpi(kpiData);
      setReports(reportsData);

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

  // Periodic polling safety net every 6s for dynamic phone-to-admin consistency
  useEffect(() => {
    const interval = setInterval(() => {
      apiService.getReports(100).then((latest) => {
        setReports((prev) => {
          // If counts or first item differs, update
          if (latest.length !== prev.length || (latest[0] && prev[0] && latest[0].id !== prev[0].id)) {
            return latest;
          }
          return prev;
        });
      }).catch(() => {});

      apiService.getSummary().then(setKpi).catch(() => {});
    }, 6000);

    return () => clearInterval(interval);
  }, []);

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

    // 4b. SOS Beacon Activated from Mobile Phone
    const unSos = registerListener('SOS_ACTIVATED', (msg) => {
      const sosItem = msg.data;
      setAlerts((prev) => [
        {
          id: `sos-${sosItem.id || Date.now()}`,
          zone_id: sosItem.zone_id,
          title: `🚨 SOS ACTIVATED - ${sosItem.zone_name || 'Emergency Zone'}`,
          message: `Reporter: ${sosItem.reporter_name || 'Anonymous'} | GPS: ${sosItem.latitude?.toFixed?.(4) ?? sosItem.latitude}, ${sosItem.longitude?.toFixed?.(4) ?? sosItem.longitude} (±${sosItem.accuracy || 10}m) | Status: RESPONSE REQUIRED`,
          alert_level: 'CRITICAL',
          is_active: true,
          created_at: sosItem.created_at || new Date().toISOString(),
        },
        ...prev.filter((a) => !a.title?.includes(sosItem.incident_id || '')),
      ]);

      // Trigger pop-up banner
      setIncomingAlertToast({
        id: String(Date.now()),
        title: `🚨 CRITICAL SOS BEACON - ${sosItem.disaster_type || 'Disaster'}`,
        description: `From ${sosItem.reporter_name || 'Citizen'} at ${sosItem.zone_name || 'Emergency Zone'}. ETA ${sosItem.eta_minutes || 8} min.`,
        type: 'SOS',
        time: new Date().toLocaleTimeString(),
      });

      apiService.getSummary().then(setKpi).catch(console.error);
    });

    // 4c. Citizen Report Received from Mobile Phone
    const unReportReceived = registerListener('REPORT_RECEIVED', (msg) => {
      const rep = msg.data;
      setReports((prev) => [
        {
          id: rep.id,
          zone_id: rep.zone_id,
          reporter_id: rep.reporter_id,
          reporter_name: rep.reporter_name || 'Citizen Reporter',
          reporter_phone: rep.reporter_phone,
          location_text: rep.location_text,
          admin_notes: rep.admin_notes,
          disaster_type: rep.disaster_type,
          description: rep.description,
          people_affected: rep.people_affected,
          injured_people: rep.injured_people,
          missing_people: rep.missing_people,
          latitude: rep.latitude,
          longitude: rep.longitude,
          photo_url: rep.photo_url,
          status: rep.status || 'PENDING REVIEW',
          priority_score: rep.priority_score,
          priority_level: rep.priority_level,
          created_at: rep.created_at || new Date().toISOString(),
          updated_at: rep.updated_at,
        },
        ...prev.filter((r) => r.id !== rep.id),
      ]);

      // Pop toast notification
      setIncomingAlertToast({
        id: rep.id,
        title: `📋 New Citizen Report: ${rep.disaster_type}`,
        description: `Affecting ~${rep.people_affected || 1} people. Reporter: ${rep.reporter_name || 'Citizen'}`,
        type: 'REPORT',
        time: new Date().toLocaleTimeString(),
      });

      apiService.getSummary().then(setKpi).catch(console.error);
    });

    // 4d. Report Updated / Accepted
    const unReportUpdated = registerListener('REPORT_UPDATED', (msg) => {
      const updated = msg.data;
      setReports((prev) =>
        prev.map((r) => (r.id === updated.id ? { ...r, ...updated } : r))
      );
    });

    // 4e. Report Deleted
    const unReportDeleted = registerListener('REPORT_DELETED', (msg) => {
      const { id } = msg.data;
      setReports((prev) => prev.filter((r) => r.id !== id));
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
      unReportReceived();
      unReportUpdated();
      unReportDeleted();
      unLog();
      unSim();
    };
  }, [registerListener, loadAllData]);

  // Report Action Handlers for instant interactive state updates
  const acceptReport = async (reportId: string, notes?: string) => {
    // Optimistic UI update
    setReports((prev) =>
      prev.map((r) => (r.id === reportId ? { ...r, status: 'VERIFIED' } : r))
    );
    try {
      const result = await apiService.acceptReport(reportId, notes);
      setReports((prev) =>
        prev.map((r) => (r.id === reportId ? result : r))
      );
      return result;
    } catch (err) {
      console.error('Failed to accept report:', err);
      loadAllData();
      throw err;
    }
  };

  const dispatchReport = async (reportId: string, data?: { notes?: string; agency_id?: string; resource_id?: string }) => {
    setReports((prev) =>
      prev.map((r) => (r.id === reportId ? { ...r, status: 'ACTIONED' } : r))
    );
    try {
      const result = await apiService.dispatchReport(reportId, data);
      setReports((prev) =>
        prev.map((r) => (r.id === reportId ? result : r))
      );
      loadAllData();
      return result;
    } catch (err) {
      console.error('Failed to dispatch report:', err);
      loadAllData();
      throw err;
    }
  };

  const resolveReport = async (reportId: string, notes?: string) => {
    setReports((prev) =>
      prev.map((r) => (r.id === reportId ? { ...r, status: 'RESOLVED' } : r))
    );
    try {
      const result = await apiService.resolveReport(reportId, notes);
      setReports((prev) =>
        prev.map((r) => (r.id === reportId ? result : r))
      );
      return result;
    } catch (err) {
      console.error('Failed to resolve report:', err);
      loadAllData();
      throw err;
    }
  };

  const dismissReport = async (reportId: string, notes?: string) => {
    setReports((prev) =>
      prev.map((r) => (r.id === reportId ? { ...r, status: 'DISMISSED' } : r))
    );
    try {
      const result = await apiService.dismissReport(reportId, notes);
      setReports((prev) =>
        prev.map((r) => (r.id === reportId ? result : r))
      );
      return result;
    } catch (err) {
      console.error('Failed to dismiss report:', err);
      loadAllData();
      throw err;
    }
  };

  const deleteReport = async (reportId: string) => {
    setReports((prev) => prev.filter((r) => r.id !== reportId));
    try {
      await apiService.deleteReport(reportId);
    } catch (err) {
      console.error('Failed to delete report:', err);
      loadAllData();
      throw err;
    }
  };

  const selectedZone = zones.find((z) => z.id === selectedZoneId) || zones[0] || null;

  return {
    zones,
    resources,
    allocations,
    needs,
    alerts,
    auditLogs,
    reports,
    kpi,
    selectedZone,
    selectedZoneId,
    setSelectedZoneId,
    loading,
    error,
    isConnected,
    incomingAlertToast,
    clearToast: () => setIncomingAlertToast(null),
    refresh: loadAllData,
    acceptReport,
    dispatchReport,
    resolveReport,
    dismissReport,
    deleteReport,
  };
}

