import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  Flame,
  Ambulance,
  HeartHandshake,
  Landmark,
  Radio,
  Clock,
  MapPin,
  Users,
  AlertTriangle,
  CheckCircle2,
  Truck,
  Navigation,
  Eye,
  X,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Activity,
  Layers,
  PhoneCall,
  Mail,
  Zap,
  Package,
  Box,
  CheckSquare,
  Ban,
} from 'lucide-react';
import { apiService } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import {
  ProviderIncident,
  ProviderKPI,
  Agency,
  Alert as AlertType,
  ResourceAllocationItem,
  ResourceInventoryItem,
} from '../types';


interface ProviderDashboardProps {}

const AGENCY_CONFIGS: Record<string, { label: string; icon: any; color: string; bg: string; border: string }> = {
  FIRE_RESCUE: {
    label: 'Fire & Rescue Department',
    icon: Flame,
    color: '#ef4444',
    bg: 'rgba(239, 68, 68, 0.12)',
    border: 'rgba(239, 68, 68, 0.3)',
  },
  POLICE: {
    label: 'Metropolitan Police Department',
    icon: ShieldAlert,
    color: '#3b82f6',
    bg: 'rgba(59, 130, 246, 0.12)',
    border: 'rgba(59, 130, 246, 0.3)',
  },
  MEDICAL: {
    label: 'City Medical Response',
    icon: Ambulance,
    color: '#10b981',
    bg: 'rgba(16, 185, 129, 0.12)',
    border: 'rgba(16, 185, 129, 0.3)',
  },
  NGO: {
    label: 'NGO Alpha Relief',
    icon: HeartHandshake,
    color: '#f59e0b',
    bg: 'rgba(245, 158, 11, 0.12)',
    border: 'rgba(245, 158, 11, 0.3)',
  },
  GOVERNMENT: {
    label: 'Government Emergency Services',
    icon: Landmark,
    color: '#a855f7',
    bg: 'rgba(168, 85, 247, 0.12)',
    border: 'rgba(168, 85, 247, 0.3)',
  },
  ALL: {
    label: 'Central Command Inter-Agency Mesh',
    icon: Layers,
    color: '#38bdf8',
    bg: 'rgba(56, 189, 248, 0.12)',
    border: 'rgba(56, 189, 248, 0.3)',
  },
};

export const ProviderDashboardPage: React.FC<ProviderDashboardProps> = () => {
  const [selectedAgencyType, setSelectedAgencyType] = useState<string>('FIRE_RESCUE');
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [incidents, setIncidents] = useState<ProviderIncident[]>([]);
  const [inventory, setInventory] = useState<ResourceInventoryItem[]>([]);
  const [allocations, setAllocations] = useState<ResourceAllocationItem[]>([]);
  const [kpis, setKpis] = useState<ProviderKPI>({
    active_incidents: 0,
    critical_incidents: 0,
    available_units: 0,
    units_deployed: 0,
    people_affected: 0,
  });
  const [alerts, setAlerts] = useState<AlertType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [selectedPhoto, setSelectedPhoto] = useState<{ url: string; incident: ProviderIncident } | null>(null);
  const [currentTime, setCurrentTime] = useState<string>(new Date().toLocaleTimeString());

  // WebSocket Live Hook
  const { isConnected, lastMessage } = useWebSocket();

  // Clock Ticker
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch initial data
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [agenciesData, kpisData, incidentsData, alertsData, invData, allocData] = await Promise.all([
        apiService.getProviderAgencies().catch(() => []),
        apiService.getProviderKPIs(selectedAgencyType).catch(() => ({
          active_incidents: 0,
          critical_incidents: 0,
          available_units: 0,
          units_deployed: 0,
          people_affected: 0,
        })),
        apiService.getProviderIncidents(selectedAgencyType).catch(() => []),
        apiService.getAlerts().catch(() => []),
        apiService.getResourceInventory(selectedAgencyType === 'ALL' ? undefined : selectedAgencyType).catch(() => []),
        apiService.getResourceAllocations(undefined, selectedAgencyType === 'ALL' ? undefined : selectedAgencyType).catch(() => []),
      ]);

      setAgencies(agenciesData);
      setKpis(kpisData);
      setIncidents(incidentsData);
      setAlerts(alertsData.slice(0, 6));
      setInventory(invData);
      setAllocations(allocData);
    } catch (err) {
      console.error('Failed to load provider data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [selectedAgencyType]);

  // Real-time WebSocket event handling
  useEffect(() => {
    if (!lastMessage) return;

    const { event, data } = lastMessage;

    if (
      event === 'SOS_ACTIVATED' ||
      event === 'PROVIDER_INCIDENT_CREATED' ||
      event === 'INCIDENT_ACCEPTED' ||
      event === 'RESOURCE_DISPATCHED' ||
      event === 'ETA_UPDATED' ||
      event === 'INCIDENT_ARRIVED' ||
      event === 'INCIDENT_RESOLVED' ||
      event === 'ZONE_UPDATED' ||
      event.startsWith('RESOURCE_')
    ) {
      // Refresh current provider state
      apiService.getProviderIncidents(selectedAgencyType).then((res) => {
        setIncidents(res);
      });
      apiService.getProviderKPIs(selectedAgencyType).then((res) => {
        setKpis(res);
      });
      apiService.getResourceInventory(selectedAgencyType === 'ALL' ? undefined : selectedAgencyType).then((res) => {
        setInventory(res);
      });
      apiService.getResourceAllocations(undefined, selectedAgencyType === 'ALL' ? undefined : selectedAgencyType).then((res) => {
        setAllocations(res);
      });
    }

    if (event === 'ALERT_CREATED' && data) {
      setAlerts((prev) => [data as AlertType, ...prev.slice(0, 5)]);
    }
  }, [lastMessage, selectedAgencyType]);

  // Provider Incident Lifecycle Action Handler
  const handleLifecycleAction = async (
    incidentId: string,
    action: 'accept' | 'dispatch' | 'enRoute' | 'arrived' | 'resolve'
  ) => {
    try {
      setActionLoadingId(incidentId);
      let updated: any;
      if (action === 'accept') {
        updated = await apiService.acceptIncident(incidentId);
      } else if (action === 'dispatch') {
        updated = await apiService.dispatchIncident(incidentId, { notes: 'Dispatched emergency strike squad.' });
      } else if (action === 'enRoute') {
        updated = await apiService.enRouteIncident(incidentId, { notes: 'Unit marked en-route.' });
      } else if (action === 'arrived') {
        updated = await apiService.arrivedIncident(incidentId, { notes: 'On-scene arrival confirmed.' });
      } else if (action === 'resolve') {
        updated = await apiService.resolveIncident(incidentId, { notes: 'Rescue operation concluded successfully.' });
      }

      if (updated && updated.incident) {
        setIncidents((prev) =>
          prev.map((inc) => (inc.incident_id === incidentId || inc.id === incidentId ? updated.incident : inc))
        );
        // Refresh KPIs
        const refreshedKPIs = await apiService.getProviderKPIs(selectedAgencyType);
        setKpis(refreshedKPIs);
      }
    } catch (err: any) {
      console.error('Lifecycle transition error:', err);
      alert(`Action failed: ${err.message || 'Error updating incident'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  // Resource Allocation Lifecycle Handler
  const handleResourceAction = async (
    allocationId: string,
    action: 'approve' | 'dispatch' | 'inTransit' | 'deliver' | 'cancel'
  ) => {
    try {
      setActionLoadingId(allocationId);
      if (action === 'approve') {
        await apiService.approveResourceAllocation(allocationId);
      } else if (action === 'dispatch') {
        await apiService.dispatchResourceAllocation(allocationId, { notes: 'Dispatched to scene via rapid vehicle' });
      } else if (action === 'inTransit') {
        await apiService.markResourceInTransit(allocationId);
      } else if (action === 'deliver') {
        await apiService.markResourceDelivered(allocationId, { notes: 'Delivered and deployed to citizens' });
      } else if (action === 'cancel') {
        await apiService.cancelResourceAllocation(allocationId, 'Cancelled and restored to inventory by provider officer');
      }

      // Reload inventory and allocations
      const [invData, allocData] = await Promise.all([
        apiService.getResourceInventory(selectedAgencyType === 'ALL' ? undefined : selectedAgencyType),
        apiService.getResourceAllocations(undefined, selectedAgencyType === 'ALL' ? undefined : selectedAgencyType),
      ]);
      setInventory(invData);
      setAllocations(allocData);
    } catch (err: any) {
      console.error('Resource action error:', err);
      alert(`Resource action failed: ${err.message || 'Error updating allocation'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const agencyConfig = AGENCY_CONFIGS[selectedAgencyType] || AGENCY_CONFIGS.FIRE_RESCUE;
  const AgencyIcon = agencyConfig.icon;

  // Active Dispatches Filter
  const activeDispatches = useMemo(() => {
    return incidents.filter((i) => ['DISPATCHED', 'EN_ROUTE', 'ARRIVED'].includes(i.provider_status));
  }, [incidents]);

  return (
    <div className="min-h-screen bg-[#070a12] text-[#f8fafc] font-sans antialiased">
      {/* Top Tactical Header */}
      <header className="border-b border-[#1e293b] bg-[#0c1220]/95 backdrop-blur sticky top-0 z-40 px-4 lg:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Logo & Agency Identity */}
          <div className="flex items-center gap-4">
            <div
              className="w-11 h-11 rounded-xl flex items-center justify-center border shadow-lg"
              style={{ backgroundColor: agencyConfig.bg, borderColor: agencyConfig.border }}
            >
              <AgencyIcon size={24} style={{ color: agencyConfig.color }} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-extrabold tracking-widest uppercase text-[#38bdf8] bg-[#0284c7]/10 px-2 py-0.5 rounded border border-[#0284c7]/30">
                  PS20
                </span>
                <span className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider">
                  EMERGENCY SERVICE PROVIDER CONSOLE
                </span>
              </div>
              <h1 className="text-lg md:text-xl font-black text-[#ffffff] tracking-tight flex items-center gap-2">
                {agencyConfig.label}
              </h1>
            </div>
          </div>

          {/* Agency Selector Dropdown & Status Controls */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Agency Tabs Selector */}
            <div className="flex items-center bg-[#070a12] border border-[#1e293b] rounded-xl p-1">
              {(['FIRE_RESCUE', 'POLICE', 'MEDICAL', 'NGO', 'GOVERNMENT', 'ALL'] as const).map((type) => {
                const conf = AGENCY_CONFIGS[type];
                const isSelected = selectedAgencyType === type;
                const Icon = conf.icon;
                return (
                  <button
                    key={type}
                    onClick={() => setSelectedAgencyType(type)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-black transition-all flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-[#1e293b] text-[#ffffff] shadow-md border border-[#334155]'
                        : 'text-[#64748b] hover:text-[#cbd5e1] hover:bg-[#0f172a]'
                    }`}
                    style={isSelected ? { color: conf.color } : {}}
                  >
                    <Icon size={14} />
                    <span className="hidden sm:inline">
                      {type === 'FIRE_RESCUE'
                        ? 'Fire'
                        : type === 'POLICE'
                        ? 'Police'
                        : type === 'MEDICAL'
                        ? 'Medical'
                        : type === 'NGO'
                        ? 'NGO'
                        : type === 'GOVERNMENT'
                        ? 'Gov'
                        : 'All Mesh'}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Live Operational Status */}
            <div className="flex items-center gap-2 bg-[#070a12] border border-[#1e293b] px-3 py-1.5 rounded-xl">
              <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-[#10b981] animate-pulse' : 'bg-[#ef4444]'}`} />
              <span className="text-xs font-black tracking-wide text-[#cbd5e1]">
                {isConnected ? 'LIVE ONLINE' : 'OFFLINE'}
              </span>
            </div>

            {/* Live Time Clock */}
            <div className="hidden lg:flex items-center gap-1.5 text-xs font-mono font-bold text-[#94a3b8] bg-[#070a12] border border-[#1e293b] px-3 py-1.5 rounded-xl">
              <Clock size={14} className="text-[#38bdf8]" />
              <span>{currentTime}</span>
            </div>

            {/* Link back to Central Command Dashboard */}
            <Link
              to="/dashboard"
              className="flex items-center gap-1.5 bg-[#0f172a] hover:bg-[#1e293b] border border-[#334155] text-[#38bdf8] text-xs font-black px-3 py-2 rounded-xl transition"
            >
              <ExternalLink size={14} />
              <span className="hidden md:inline">Authority Central Command</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 lg:px-8 py-6 space-y-6">
        {/* KPI Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
          {/* Active Incidents */}
          <div className="bg-[#0c1220] border border-[#1e293b] rounded-2xl p-4 flex flex-col justify-between relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-16 h-16 bg-red-500/5 rounded-full blur-xl group-hover:bg-red-500/10 transition" />
            <div className="text-xs font-extrabold uppercase tracking-wider text-[#94a3b8] flex items-center justify-between">
              <span>Active Incidents</span>
              <Activity size={16} className="text-[#f87171]" />
            </div>
            <div className="mt-2 text-2xl md:text-3xl font-black text-[#ffffff]">{kpis.active_incidents}</div>
            <div className="mt-1 text-[11px] font-bold text-[#ef4444]">Response Needed</div>
          </div>

          {/* Critical Incidents */}
          <div className="bg-[#0c1220] border border-[#ef4444]/30 rounded-2xl p-4 flex flex-col justify-between relative overflow-hidden group bg-gradient-to-br from-red-950/20 to-transparent">
            <div className="text-xs font-extrabold uppercase tracking-wider text-[#fca5a5] flex items-center justify-between">
              <span>Critical Incidents</span>
              <ShieldAlert size={16} className="text-[#ef4444] animate-bounce" />
            </div>
            <div className="mt-2 text-2xl md:text-3xl font-black text-[#ef4444]">{kpis.critical_incidents}</div>
            <div className="mt-1 text-[11px] font-bold text-[#f87171]">Severity &gt;= 8.0</div>
          </div>

          {/* Available Units */}
          <div className="bg-[#0c1220] border border-[#1e293b] rounded-2xl p-4 flex flex-col justify-between relative overflow-hidden">
            <div className="text-xs font-extrabold uppercase tracking-wider text-[#94a3b8] flex items-center justify-between">
              <span>Available Units</span>
              <Truck size={16} className="text-[#34d399]" />
            </div>
            <div className="mt-2 text-2xl md:text-3xl font-black text-[#10b981]">{kpis.available_units}</div>
            <div className="mt-1 text-[11px] font-bold text-[#34d399]">Ready for Dispatch</div>
          </div>

          {/* Units Deployed */}
          <div className="bg-[#0c1220] border border-[#1e293b] rounded-2xl p-4 flex flex-col justify-between relative overflow-hidden">
            <div className="text-xs font-extrabold uppercase tracking-wider text-[#94a3b8] flex items-center justify-between">
              <span>Units Deployed</span>
              <Navigation size={16} className="text-[#38bdf8]" />
            </div>
            <div className="mt-2 text-2xl md:text-3xl font-black text-[#38bdf8]">{kpis.units_deployed}</div>
            <div className="mt-1 text-[11px] font-bold text-[#38bdf8]">Active Wheels-Up</div>
          </div>

          {/* People Affected */}
          <div className="bg-[#0c1220] border border-[#1e293b] rounded-2xl p-4 flex flex-col justify-between relative overflow-hidden col-span-2 md:col-span-1">
            <div className="text-xs font-extrabold uppercase tracking-wider text-[#94a3b8] flex items-center justify-between">
              <span>People Affected</span>
              <Users size={16} className="text-[#fbbf24]" />
            </div>
            <div className="mt-2 text-2xl md:text-3xl font-black text-[#fbbf24]">{kpis.people_affected}</div>
            <div className="mt-1 text-[11px] font-bold text-[#f59e0b]">In Sector Zones</div>
          </div>
        </div>

        {/* Agency Inventory Stock Monitor */}
        <div className="bg-[#0c1220] border border-[#1e293b] rounded-2xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1e293b] pb-3">
            <div className="flex items-center gap-2">
              <Package size={18} className="text-[#38bdf8]" />
              <h3 className="text-sm font-black uppercase tracking-wider text-[#ffffff]">
                {agencyConfig.label} — Live Resource Inventory ({inventory.length} Categories)
              </h3>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Row-Locked Real Decrements • Zero Over-Allocation
            </span>
          </div>

          {inventory.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">
              No inventory tracked for this agency type.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {inventory.map((item) => {
                const avail = item.available_quantity;
                const total = item.total_quantity;
                const pct = total > 0 ? Math.round((avail / total) * 100) : 0;
                const isLow = pct < 20;

                return (
                  <div
                    key={item.id}
                    className={`bg-[#070a12] border rounded-xl p-3.5 space-y-2.5 transition relative overflow-hidden ${
                      isLow ? 'border-red-500/40' : 'border-[#1e293b]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-xs text-slate-100">{item.resource_name}</span>
                      <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-[#1e293b] text-sky-400">
                        {item.resource_type}
                      </span>
                    </div>

                    <div className="flex items-baseline justify-between text-xs font-mono">
                      <span className="text-slate-400">Available:</span>
                      <span className={`text-base font-black ${isLow ? 'text-red-400' : 'text-emerald-400'}`}>
                        {avail} <span className="text-[10px] font-normal text-slate-400">/ {total} {item.unit}</span>
                      </span>
                    </div>

                    {/* Stock Bar */}
                    <div className="w-full bg-[#1e293b] h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          pct < 20 ? 'bg-red-500' : pct < 50 ? 'bg-amber-500' : 'bg-emerald-500'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono pt-0.5">
                      <span>Allocated: {item.allocated_quantity}</span>
                      <span className={`font-bold ${avail === 0 ? 'text-red-400 animate-pulse' : 'text-slate-300'}`}>
                        {avail === 0 ? 'DEPLETED' : `${pct}% READY`}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Core Layout: Incidents on Left (2/3), Dispatches & Live Feed on Right (1/3) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* LEFT: Critical Incidents Queue (7 Cols) */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#ef4444] animate-ping" />
                <h2 className="text-base font-black uppercase tracking-wider text-[#ffffff]">
                  CRITICAL INCIDENTS & DISPATCH QUEUE ({incidents.length})
                </h2>
              </div>
              <button
                onClick={loadDashboardData}
                className="text-xs font-bold text-[#94a3b8] hover:text-[#38bdf8] flex items-center gap-1 transition"
              >
                <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
                Refresh
              </button>
            </div>

            {loading && incidents.length === 0 ? (
              <div className="bg-[#0c1220] border border-[#1e293b] rounded-2xl p-12 text-center text-[#94a3b8]">
                <RefreshCw size={28} className="animate-spin mx-auto text-[#38bdf8] mb-3" />
                <p className="font-bold text-sm">Syncing live emergency incidents with mesh...</p>
              </div>
            ) : incidents.length === 0 ? (
              <div className="bg-[#0c1220] border border-[#1e293b] rounded-2xl p-12 text-center space-y-3">
                <CheckCircle2 size={36} className="mx-auto text-[#10b981]" />
                <h3 className="text-base font-black text-[#ffffff]">All Sector Incidents Cleared</h3>
                <p className="text-xs text-[#94a3b8] max-w-md mx-auto">
                  No pending critical alarms assigned for {agencyConfig.label}. Live WebSocket channel will alert on
                  citizen SOS transmission.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {incidents.map((incident) => {
                  const isResolved = incident.provider_status === 'RESOLVED';
                  const isCritical = incident.severity >= 8.0;

                  // Find allocations for this incident
                  const incidentAllocations = allocations.filter(
                    (a) => a.incident_id === incident.incident_id || a.sos_id === incident.id
                  );

                  return (
                    <div
                      key={incident.id || incident.incident_id}
                      className={`bg-[#0c1220] border rounded-2xl p-5 space-y-4 transition-all relative overflow-hidden ${
                        isResolved
                          ? 'border-[#1e293b] opacity-75'
                          : isCritical
                          ? 'border-red-500/40 hover:border-red-500/70 shadow-lg shadow-red-950/20'
                          : 'border-[#1e293b] hover:border-[#334155]'
                      }`}
                    >
                      {/* Top Row: Incident ID + Type + Status */}
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1e293b] pb-3">
                        <div className="flex items-center gap-3">
                          <span className="font-mono font-black text-sm text-[#ffffff] bg-[#1e293b] px-2.5 py-1 rounded-lg border border-[#334155]">
                            {incident.incident_id}
                          </span>
                          <span
                            className={`text-xs font-black uppercase px-2.5 py-1 rounded-lg ${
                              incident.disaster_type.toLowerCase().includes('flood')
                                ? 'bg-blue-500/15 text-[#60a5fa] border border-blue-500/30'
                                : incident.disaster_type.toLowerCase().includes('fire')
                                ? 'bg-red-500/15 text-[#f87171] border border-red-500/30'
                                : incident.disaster_type.toLowerCase().includes('earthquake')
                                ? 'bg-amber-500/15 text-[#fbbf24] border border-amber-500/30'
                                : 'bg-emerald-500/15 text-[#34d399] border border-emerald-500/30'
                            }`}
                          >
                            {incident.disaster_type} — {isCritical ? 'CRITICAL' : 'HIGH'}
                          </span>
                        </div>

                        {/* Provider Status Pill */}
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-xs font-black px-3 py-1 rounded-full uppercase tracking-wider ${
                              incident.provider_status === 'NEW'
                                ? 'bg-red-500/20 text-[#f87171] border border-red-500/50 animate-pulse'
                                : incident.provider_status === 'ACCEPTED'
                                ? 'bg-amber-500/20 text-[#fbbf24] border border-amber-500/40'
                                : incident.provider_status === 'DISPATCHED'
                                ? 'bg-sky-500/20 text-[#38bdf8] border border-sky-500/40'
                                : incident.provider_status === 'EN_ROUTE'
                                ? 'bg-indigo-500/20 text-[#818cf8] border border-indigo-500/40 animate-pulse'
                                : incident.provider_status === 'ARRIVED'
                                ? 'bg-purple-500/20 text-[#c084fc] border border-purple-500/40'
                                : 'bg-emerald-500/20 text-[#34d399] border border-emerald-500/40'
                            }`}
                          >
                            ● {incident.provider_status}
                          </span>
                        </div>
                      </div>

                      {/* Main Incident Details Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                        {/* Location & Zone */}
                        <div className="space-y-1">
                          <span className="text-[#64748b] font-extrabold uppercase">Zone & Coordinates</span>
                          <div className="font-bold text-[#f8fafc] flex items-center gap-1.5">
                            <MapPin size={14} className="text-[#ef4444]" />
                            <span>{incident.zone_name}</span>
                          </div>
                          <div className="font-mono text-[#94a3b8] text-[11px] pl-5">{incident.location_text}</div>
                        </div>

                        {/* Casualties */}
                        <div className="space-y-1">
                          <span className="text-[#64748b] font-extrabold uppercase">Casualties & Victims</span>
                          <div className="font-bold text-[#ffffff] flex items-center gap-2">
                            <span className="text-[#f87171]">{incident.people_affected} Affected</span>
                            <span>•</span>
                            <span className="text-[#fbbf24]">{incident.injured_people} Injured</span>
                            <span>•</span>
                            <span className="text-[#94a3b8]">{incident.missing_people} Missing</span>
                          </div>
                          <div className="text-[11px] text-[#38bdf8] font-bold flex items-center gap-2">
                            <span>Severity: {incident.severity}/10.0</span>
                            {incident.priority_score !== undefined && incident.priority_score !== null && (
                              <span className="text-amber-400 font-extrabold">• Priority Score: {incident.priority_score.toFixed(2)} ({incident.priority_level || 'HIGH'})</span>
                            )}
                          </div>
                          {incident.priority_assessment?.components && (
                            <div className="text-[10px] text-[#94a3b8] font-mono mt-0.5">
                              Ppl: +{incident.priority_assessment.components.affected_people.score.toFixed(2)} | 
                              Dst: +{incident.priority_assessment.components.disaster_type.score.toFixed(2)} | 
                              Urg: +{incident.priority_assessment.components.urgency_keywords.score.toFixed(2)}
                            </div>
                          )}
                        </div>

                        {/* Distance & Dynamic ETA */}
                        <div className="space-y-1">
                          <span className="text-[#64748b] font-extrabold uppercase">Response Telemetry</span>
                          <div className="font-black text-[#38bdf8] text-sm flex items-center gap-1.5">
                            <Navigation size={14} className="text-[#38bdf8]" />
                            <span>
                              {incident.distance_km} km • ETA: {incident.eta_minutes} min
                            </span>
                          </div>
                          <div className="text-[11px] text-[#10b981] font-bold">
                            Unit: {incident.assigned_resource_name || 'Rapid Response Unit'}
                          </div>
                        </div>
                      </div>

                      {/* Granular Resource Allotment Breakdown & Controls */}
                      {incidentAllocations.length > 0 && (
                        <div className="bg-[#070a12] border border-[#1e293b] rounded-xl p-3 space-y-2.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-slate-300 flex items-center gap-1.5">
                              <Box size={14} className="text-sky-400" />
                              Assigned Resources & Allotment Manifest
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono">
                              Tri-Level Accounting (Req vs Rec vs Alloc)
                            </span>
                          </div>

                          <div className="space-y-2">
                            {incidentAllocations.map((alloc) => {
                              const isAllocated = alloc.status === 'ALLOCATED';
                              const isPartial = alloc.status === 'PARTIALLY_ALLOCATED';
                              const isDispatched = alloc.status === 'DISPATCHED';
                              const isInTransit = alloc.status === 'IN_TRANSIT';
                              const isDelivered = alloc.status === 'DELIVERED';
                              const isCancelled = alloc.status === 'CANCELLED';
                              const isUnavailable = alloc.status === 'UNAVAILABLE';

                              return (
                                <div
                                  key={alloc.id}
                                  className="bg-[#0c1220] border border-[#1e293b] p-2.5 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
                                >
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                      <span className="font-bold text-slate-100">{alloc.resource_type}</span>
                                      <span className="text-[11px] text-slate-400 font-mono">
                                        ({alloc.resource_name || alloc.unit})
                                      </span>
                                      <span
                                        className={`text-[10px] font-black px-2 py-0.5 rounded uppercase font-mono ${
                                          isDelivered
                                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                                            : isInTransit
                                            ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 animate-pulse'
                                            : isDispatched
                                            ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40'
                                            : isAllocated
                                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                            : isPartial
                                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                                            : isUnavailable
                                            ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                                            : 'bg-slate-800 text-slate-400 border-slate-700'
                                        }`}
                                      >
                                        {alloc.status}
                                      </span>
                                    </div>
                                    <div className="text-[11px] text-slate-400 font-mono flex flex-wrap gap-2">
                                      <span>Req: <strong className="text-slate-200">{alloc.requested_quantity}</strong></span>
                                      <span>•</span>
                                      <span>Rec: <strong className="text-slate-200">{alloc.recommended_quantity}</strong></span>
                                      <span>•</span>
                                      <span>Alloc: <strong className="text-sky-300">{alloc.allocated_quantity} {alloc.unit}</strong></span>
                                      {alloc.notes && <span className="text-slate-500">({alloc.notes})</span>}
                                    </div>
                                  </div>

                                  {/* Resource Allocation Action Buttons */}
                                  <div className="flex items-center gap-1.5 self-end md:self-center">
                                    {(alloc.status === 'REQUESTED' || alloc.status === 'RECOMMENDED') && (
                                      <button
                                        onClick={() => handleResourceAction(alloc.id, 'approve')}
                                        disabled={actionLoadingId === alloc.id}
                                        className="bg-sky-600 hover:bg-sky-500 text-white font-bold text-[11px] px-2.5 py-1 rounded transition flex items-center gap-1"
                                      >
                                        <CheckSquare size={12} />
                                        Approve
                                      </button>
                                    )}

                                    {(isAllocated || isPartial) && (
                                      <button
                                        onClick={() => handleResourceAction(alloc.id, 'dispatch')}
                                        disabled={actionLoadingId === alloc.id}
                                        className="bg-sky-600 hover:bg-sky-500 text-white font-bold text-[11px] px-2.5 py-1 rounded transition flex items-center gap-1"
                                      >
                                        <Truck size={12} />
                                        Dispatch
                                      </button>
                                    )}

                                    {isDispatched && (
                                      <button
                                        onClick={() => handleResourceAction(alloc.id, 'inTransit')}
                                        disabled={actionLoadingId === alloc.id}
                                        className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[11px] px-2.5 py-1 rounded transition flex items-center gap-1"
                                      >
                                        <Navigation size={12} />
                                        In-Transit
                                      </button>
                                    )}

                                    {isInTransit && (
                                      <button
                                        onClick={() => handleResourceAction(alloc.id, 'deliver')}
                                        disabled={actionLoadingId === alloc.id}
                                        className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[11px] px-2.5 py-1 rounded transition flex items-center gap-1"
                                      >
                                        <CheckCircle2 size={12} />
                                        Deliver
                                      </button>
                                    )}

                                    {!isDelivered && !isCancelled && (
                                      <button
                                        onClick={() => handleResourceAction(alloc.id, 'cancel')}
                                        disabled={actionLoadingId === alloc.id}
                                        className="bg-slate-800 hover:bg-red-950 text-slate-400 hover:text-red-300 font-bold text-[11px] px-2 py-1 rounded border border-slate-700 hover:border-red-500/40 transition flex items-center gap-1"
                                        title="Cancel and restore inventory"
                                      >
                                        <Ban size={12} />
                                        Cancel
                                      </button>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Required Resources Chips & Notification Indicators */}
                      <div className="flex flex-wrap items-center justify-between gap-2 bg-[#070a12] p-3 rounded-xl border border-[#1e293b]">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-[11px] font-bold text-[#64748b] mr-1">Required:</span>
                          {incident.required_resources.map((res, idx) => (
                            <span
                              key={idx}
                              className="text-[11px] font-extrabold text-[#38bdf8] bg-[#0284c7]/10 border border-[#0284c7]/20 px-2 py-0.5 rounded-md"
                            >
                              {res}
                            </span>
                          ))}
                        </div>

                        {/* Resend & PagerDuty Delivery Tags */}
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[10px] font-extrabold px-2 py-0.5 rounded border flex items-center gap-1 ${
                              incident.resend_status === 'SENT'
                                ? 'bg-emerald-500/10 text-[#34d399] border-emerald-500/30'
                                : incident.resend_status === 'DEMO'
                                ? 'bg-amber-500/10 text-[#fbbf24] border-amber-500/30'
                                : 'bg-slate-800 text-[#94a3b8] border-[#334155]'
                            }`}
                          >
                            <Mail size={10} />
                            Email: {incident.resend_status}
                          </span>

                          <span
                            className={`text-[10px] font-extrabold px-2 py-0.5 rounded border flex items-center gap-1 ${
                              incident.pagerduty_status === 'SENT'
                                ? 'bg-emerald-500/10 text-[#34d399] border-emerald-500/30'
                                : incident.pagerduty_status === 'DEMO'
                                ? 'bg-amber-500/10 text-[#fbbf24] border-amber-500/30'
                                : 'bg-slate-800 text-[#94a3b8] border-[#334155]'
                            }`}
                          >
                            <PhoneCall size={10} />
                            PagerDuty: {incident.pagerduty_status}
                          </span>

                          {incident.photo_url && (
                            <button
                              onClick={() => setSelectedPhoto({ url: incident.photo_url!, incident })}
                              className="text-[10px] font-extrabold px-2.5 py-0.5 rounded bg-sky-500/15 text-[#38bdf8] border border-sky-500/30 hover:bg-sky-500/25 transition flex items-center gap-1"
                            >
                              <Eye size={10} />
                              View Photo
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Action Lifecycle Buttons (State-Driven) */}
                      <div className="flex flex-wrap items-center justify-end gap-2.5 pt-2">
                        {incident.provider_status === 'NEW' && (
                          <button
                            onClick={() => handleLifecycleAction(incident.incident_id, 'accept')}
                            disabled={actionLoadingId === incident.incident_id}
                            className="bg-[#ef4444] hover:bg-[#dc2626] text-[#ffffff] font-black text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-red-950/30 transition flex items-center gap-2"
                          >
                            <CheckCircle2 size={14} />
                            [ACCEPT INCIDENT]
                          </button>
                        )}

                        {incident.provider_status === 'ACCEPTED' && (
                          <button
                            onClick={() => handleLifecycleAction(incident.incident_id, 'dispatch')}
                            disabled={actionLoadingId === incident.incident_id}
                            className="bg-[#0284c7] hover:bg-[#0369a1] text-[#ffffff] font-black text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-sky-950/30 transition flex items-center gap-2"
                          >
                            <Truck size={14} />
                            [DISPATCH UNIT]
                          </button>
                        )}

                        {incident.provider_status === 'DISPATCHED' && (
                          <button
                            onClick={() => handleLifecycleAction(incident.incident_id, 'enRoute')}
                            disabled={actionLoadingId === incident.incident_id}
                            className="bg-[#6366f1] hover:bg-[#4f46e5] text-[#ffffff] font-black text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-indigo-950/30 transition flex items-center gap-2"
                          >
                            <Navigation size={14} />
                            [MARK EN ROUTE]
                          </button>
                        )}

                        {incident.provider_status === 'EN_ROUTE' && (
                          <button
                            onClick={() => handleLifecycleAction(incident.incident_id, 'arrived')}
                            disabled={actionLoadingId === incident.incident_id}
                            className="bg-[#9333ea] hover:bg-[#7e22ce] text-[#ffffff] font-black text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-purple-950/30 transition flex items-center gap-2"
                          >
                            <MapPin size={14} />
                            [MARK ARRIVED ON-SCENE]
                          </button>
                        )}

                        {incident.provider_status === 'ARRIVED' && (
                          <button
                            onClick={() => handleLifecycleAction(incident.incident_id, 'resolve')}
                            disabled={actionLoadingId === incident.incident_id}
                            className="bg-[#10b981] hover:bg-[#059669] text-[#ffffff] font-black text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-emerald-950/30 transition flex items-center gap-2"
                          >
                            <CheckCircle2 size={14} />
                            [RESOLVE INCIDENT]
                          </button>
                        )}

                        {incident.provider_status === 'RESOLVED' && (
                          <div className="text-xs font-extrabold text-[#34d399] flex items-center gap-1.5 bg-emerald-500/10 px-4 py-2 rounded-xl border border-emerald-500/20">
                            <CheckCircle2 size={14} />
                            Incident Successfully Resolved
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: Active Dispatches & Live Alerts (5 Cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Active Dispatches Progress Board */}
            <div className="bg-[#0c1220] border border-[#1e293b] rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1e293b] pb-3">
                <div className="flex items-center gap-2">
                  <Truck size={18} className="text-[#38bdf8]" />
                  <h3 className="text-sm font-black uppercase tracking-wider text-[#ffffff]">
                    ACTIVE DISPATCHES ({activeDispatches.length})
                  </h3>
                </div>
                <span className="text-[11px] font-bold text-[#94a3b8]">Live GPS Fleet</span>
              </div>

              {activeDispatches.length === 0 ? (
                <div className="p-6 text-center text-xs text-[#64748b]">
                  No active units currently en route in this sector.
                </div>
              ) : (
                <div className="space-y-3">
                  {activeDispatches.map((disp) => (
                    <div
                      key={disp.id}
                      className="bg-[#070a12] border border-[#1e293b] rounded-xl p-3.5 space-y-2.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-extrabold text-xs text-[#ffffff]">
                          {disp.assigned_resource_name || 'Response Squad 01'}
                        </span>
                        <span className="text-[10px] font-black px-2 py-0.5 rounded bg-[#0284c7]/20 text-[#38bdf8] border border-[#0284c7]/40">
                          {disp.provider_status}
                        </span>
                      </div>

                      <div className="text-[11px] text-[#94a3b8] flex items-center justify-between">
                        <span>Dest: {disp.zone_name}</span>
                        <span className="font-black text-[#38bdf8]">
                          {disp.distance_km} km • ETA: {disp.eta_minutes}m
                        </span>
                      </div>

                      {/* Animated Progress Bar */}
                      <div className="w-full bg-[#1e293b] h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-[#0284c7] to-[#38bdf8] h-full rounded-full transition-all duration-500 animate-pulse"
                          style={{
                            width:
                              disp.provider_status === 'ARRIVED'
                                ? '100%'
                                : disp.provider_status === 'EN_ROUTE'
                                ? '65%'
                                : '30%',
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Live Tactical Alerts Feed */}
            <div className="bg-[#0c1220] border border-[#1e293b] rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1e293b] pb-3">
                <div className="flex items-center gap-2">
                  <Radio size={18} className="text-[#f87171] animate-pulse" />
                  <h3 className="text-sm font-black uppercase tracking-wider text-[#ffffff]">
                    REAL-TIME ALERTS & TELEMETRY
                  </h3>
                </div>
              </div>

              <div className="space-y-2.5">
                {alerts.map((al) => (
                  <div
                    key={al.id}
                    className={`p-3 rounded-xl border text-xs space-y-1 ${
                      al.alert_level === 'CRITICAL'
                        ? 'bg-red-950/20 border-red-500/30 text-red-200'
                        : al.alert_level === 'WARNING'
                        ? 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                        : 'bg-[#070a12] border-[#1e293b] text-[#cbd5e1]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-black uppercase text-[11px] flex items-center gap-1.5">
                        <AlertTriangle size={12} className={al.alert_level === 'CRITICAL' ? 'text-[#ef4444]' : 'text-[#fbbf24]'} />
                        {al.title}
                      </span>
                      <span className="text-[10px] text-[#64748b]">
                        {new Date(al.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-[11px] opacity-90 leading-relaxed">{al.message}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Scenario Injection Quick Test */}
            <div className="bg-[#0c1220] border border-[#1e293b] rounded-2xl p-5 space-y-3">
              <div className="flex items-center gap-2">
                <Zap size={16} className="text-[#fbbf24]" />
                <h4 className="text-xs font-black uppercase tracking-wider text-[#ffffff]">
                  DEMO SURGE SIMULATION
                </h4>
              </div>
              <p className="text-[11px] text-[#94a3b8]">
                Injects high-severity Zone A flood with trapped victims, multi-agency routing, and automated notification
                escalation.
              </p>
              <button
                onClick={async () => {
                  try {
                    await apiService.injectEmergency();
                    await loadDashboardData();
                  } catch (e: any) {
                    alert('Simulation injection error: ' + e.message);
                  }
                }}
                className="w-full bg-[#1e293b] hover:bg-[#334155] border border-[#334155] text-[#fbbf24] text-xs font-black py-2.5 rounded-xl transition flex items-center justify-center gap-2"
              >
                <Zap size={14} />
                [TRIGGER DEMO CRITICAL EMERGENCY]
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Incident Photo Modal (Full Resolution Evidence View) */}
      {selectedPhoto && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0c1220] border border-[#334155] rounded-2xl max-w-2xl w-full overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#1e293b]">
              <div>
                <span className="text-xs font-extrabold text-[#38bdf8] uppercase">CITIZEN EVIDENCE PHOTO</span>
                <h3 className="text-base font-black text-[#ffffff]">
                  Incident {selectedPhoto.incident.incident_id} ({selectedPhoto.incident.disaster_type})
                </h3>
              </div>
              <button
                onClick={() => setSelectedPhoto(null)}
                className="p-1.5 rounded-lg bg-[#1e293b] text-[#94a3b8] hover:text-[#ffffff] transition"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-4 bg-[#070a12] flex items-center justify-center max-h-[65vh] overflow-hidden">
              <img
                src={selectedPhoto.url}
                alt="Emergency Incident Evidence"
                className="max-h-[60vh] max-w-full object-contain rounded-lg border border-[#1e293b]"
                onError={(e: any) => {
                  e.target.src = 'https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80';
                }}
              />
            </div>

            <div className="px-5 py-4 bg-[#0c1220] border-t border-[#1e293b] flex flex-wrap items-center justify-between text-xs text-[#94a3b8] gap-3">
              <div>
                Location: <span className="font-bold text-[#ffffff]">{selectedPhoto.incident.zone_name}</span> (
                {selectedPhoto.incident.location_text})
              </div>
              <a
                href={selectedPhoto.url}
                target="_blank"
                rel="noreferrer"
                className="text-[#38bdf8] font-bold hover:underline flex items-center gap-1"
              >
                <ExternalLink size={12} />
                Open Original Image
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
