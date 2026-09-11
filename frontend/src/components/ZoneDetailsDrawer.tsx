import React from 'react';
import { Zone, Allocation } from '../types';
import { getSeverityColor } from '../utils/formatters';
import {
  ShieldAlert,
  Users,
  Clock,
  Truck,
  Activity,
  CheckCircle2,
  FileText,
  AlertTriangle,
  Flame,
  Waves,
  Wind,
} from 'lucide-react';
import { StatusBadge } from './StatusBadge';

interface ZoneDetailsDrawerProps {
  zone: Zone | null;
  allocations: Allocation[];
  onClose?: () => void;
}

export const ZoneDetailsDrawer: React.FC<ZoneDetailsDrawerProps> = ({ zone, allocations }) => {
  if (!zone) {
    return (
      <div className="p-6 rounded-xl bg-ops-card border border-ops-border text-center text-slate-400">
        <ShieldAlert className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">Select a disaster zone on the map or table to view operational telemetry.</p>
      </div>
    );
  }

  const sevColor = getSeverityColor(zone.overall_severity);
  const zoneAllocations = allocations.filter((a) => a.zone_id === zone.id);

  const getDisasterIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'flood':
        return <Waves className="w-5 h-5 text-sky-400" />;
      case 'earthquake':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'cyclone':
        return <Wind className="w-5 h-5 text-teal-400" />;
      case 'fire':
        return <Flame className="w-5 h-5 text-rose-400" />;
      default:
        return <ShieldAlert className="w-5 h-5 text-red-400" />;
    }
  };

  return (
    <div className="bg-ops-card border border-ops-border rounded-xl p-5 space-y-5 shadow-lg">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-ops-border pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
              {getDisasterIcon(zone.disaster_type)}
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">{zone.name}</h2>
              <div className="flex items-center space-x-2 text-xs text-slate-400">
                <span>Hazard: {zone.disaster_type}</span>
                <span>•</span>
                <span className="font-mono">
                  {zone.latitude.toFixed(4)}°N, {zone.longitude.toFixed(4)}°E
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="text-right">
          <div
            className={`inline-flex items-center px-2.5 py-1 rounded-lg border font-mono font-bold text-xs ${sevColor.bg} ${sevColor.text} ${sevColor.border} ${sevColor.glow}`}
          >
            SEVERITY {zone.overall_severity.toFixed(1)} / 10
          </div>
          <div className="text-[11px] text-slate-400 mt-1 uppercase font-semibold">
            Status: <span className="text-slate-200">{zone.status}</span>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
            <Users className="w-3.5 h-3.5 text-indigo-400" />
            <span>Affected Population</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {zone.affected_people.toLocaleString()}
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
            <Truck className="w-3.5 h-3.5 text-sky-400" />
            <span>Active Deployments</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">{zoneAllocations.length} Units</div>
        </div>
      </div>

      {/* Individual Resource Needs */}
      <div>
        <div className="flex items-center justify-between mb-2.5">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
            <Activity className="w-3.5 h-3.5 text-rose-400" />
            <span>Critical Needs Breakdown</span>
          </span>
          <span className="text-[11px] text-slate-500 font-mono">
            {zone.needs?.length || 0} Priorities
          </span>
        </div>

        <div className="space-y-2">
          {zone.needs && zone.needs.length > 0 ? (
            zone.needs.map((need) => {
              const needSev = getSeverityColor(need.severity);
              const progressPct = Math.min(
                100,
                Math.round((need.quantity_fulfilled / (need.quantity_required || 1)) * 100)
              );

              return (
                <div
                  key={need.id}
                  className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1.5"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">{need.resource_type}</span>
                    <div className="flex items-center space-x-2">
                      <span
                        className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${needSev.bg} ${needSev.text} ${needSev.border}`}
                      >
                        Priority {need.priority_score.toFixed(1)}
                      </span>
                      <StatusBadge status={need.status} />
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                      <span>
                        Fulfilled: {need.quantity_fulfilled} / {need.quantity_required}
                      </span>
                      <span>{progressPct}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          progressPct >= 80 ? 'bg-emerald-500' : progressPct >= 40 ? 'bg-sky-500' : 'bg-rose-500'
                        }`}
                        style={{ width: `${progressPct}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <p className="text-xs text-slate-500 italic">No specific needs logged for this zone.</p>
          )}
        </div>
      </div>

      {/* Active Allocations & ETA */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>Assigned Resource ETAs</span>
          </span>
        </div>

        {zoneAllocations.length > 0 ? (
          <div className="space-y-2">
            {zoneAllocations.map((alloc) => (
              <div
                key={alloc.id}
                className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-medium text-slate-200">
                    {alloc.resource?.name || 'Mobilized Unit'}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {alloc.resource?.agency?.name || 'Emergency Agency'} • Qty: {alloc.quantity}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-amber-400 flex items-center justify-end space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>{alloc.eta_minutes ?? 15} min</span>
                  </div>
                  <StatusBadge status={alloc.status} className="mt-0.5" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800 text-xs text-slate-400 text-center">
            No active units en route. Allocations will appear once dispatched.
          </div>
        )}
      </div>

      {/* Latest Report Snippet */}
      <div>
        <div className="flex items-center space-x-1.5 text-xs font-mono font-bold uppercase tracking-wider text-slate-300 mb-2">
          <FileText className="w-3.5 h-3.5 text-sky-400" />
          <span>Latest Field Incident</span>
        </div>
        <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-300 leading-relaxed">
          {zone.reports && zone.reports.length > 0 ? (
            <div>
              <p className="font-normal text-slate-300">{zone.reports[0].description}</p>
              <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-slate-800 text-[10px] text-slate-400">
                <span>Casualties reported: ~{zone.reports[0].people_affected}</span>
                <span className="text-emerald-400 font-semibold">{zone.reports[0].status}</span>
              </div>
            </div>
          ) : (
            <p className="italic text-slate-500">
              Primary survey: Sector under active monitoring. Water levels stable at 1.2m above warning datum.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
