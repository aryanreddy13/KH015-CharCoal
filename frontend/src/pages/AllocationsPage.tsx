import React from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import { StatusBadge } from '../components/StatusBadge';
import { Split, Clock, Navigation, MapPin, Building2 } from 'lucide-react';

export const AllocationsPage: React.FC = () => {
  const { allocations, zones } = useDashboardData();

  const getZoneName = (zoneId: string) => {
    const found = zones.find((z) => z.id === zoneId);
    return found ? found.name : 'Unknown Zone';
  };

  return (
    <div className="space-y-4 max-w-[1700px] mx-auto pb-8">
      {/* Page Header */}
      <div className="flex items-center justify-between border-b border-ops-border pb-3">
        <div>
          <h1 className="text-lg font-bold text-white font-mono flex items-center space-x-2">
            <Split className="w-5 h-5 text-sky-400" />
            <span>ACTIVE DISPATCHES & ALLOCATIONS</span>
          </h1>
          <p className="text-xs text-slate-400">
            Real-time convoy tracking, corridor travel estimates, and agency dispatch manifests.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-300 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          Active Convoys: <span className="text-amber-400 font-bold">{allocations.length}</span>
        </div>
      </div>

      {/* Allocations Table */}
      <div className="rounded-xl bg-ops-card border border-ops-border overflow-hidden shadow-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-[11px] font-mono uppercase text-slate-400 border-b border-ops-border">
              <tr>
                <th className="py-3 px-4">Convoy / Resource</th>
                <th className="py-3 px-4">Deploying Agency</th>
                <th className="py-3 px-4">Destination Sector</th>
                <th className="py-3 px-4">Need Category</th>
                <th className="py-3 px-4">Quantity</th>
                <th className="py-3 px-4">Distance (KM)</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Computed ETA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {allocations.length > 0 ? (
                allocations.map((alloc) => (
                  <tr key={alloc.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-100">
                      <div className="flex items-center space-x-2">
                        <Navigation className="w-3.5 h-3.5 text-sky-400 transform rotate-45" />
                        <span>{alloc.resource?.name || 'Mobilized Unit'}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {alloc.resource?.agency?.name || 'Emergency Services'}
                    </td>
                    <td className="py-3 px-4 text-slate-200 font-medium">
                      <div className="flex items-center space-x-1">
                        <MapPin className="w-3 h-3 text-rose-500 flex-shrink-0" />
                        <span>{getZoneName(alloc.zone_id)}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {alloc.resource?.resource_type || 'General Relief'}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-slate-200">
                      {alloc.quantity}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400">
                      {alloc.distance_km ? `${alloc.distance_km} km` : '5.2 km'}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={alloc.status} />
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-amber-400">
                      <span className="inline-flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-amber-500" />
                        <span>{alloc.eta_minutes ?? 15} min</span>
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No active dispatches currently en route.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
