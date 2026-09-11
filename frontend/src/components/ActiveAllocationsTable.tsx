import React from 'react';
import { Allocation, Zone } from '../types';
import { StatusBadge } from './StatusBadge';
import { Split, Clock, Navigation, MapPin } from 'lucide-react';

interface ActiveAllocationsTableProps {
  allocations: Allocation[];
  zones: Zone[];
  onSelectZone?: (zoneId: string) => void;
}

export const ActiveAllocationsTable: React.FC<ActiveAllocationsTableProps> = ({
  allocations,
  zones,
  onSelectZone,
}) => {
  const getZoneName = (zoneId: string) => {
    const found = zones.find((z) => z.id === zoneId);
    return found ? found.name.split(' - ')[0] : 'Emergency Zone';
  };

  return (
    <div className="rounded-xl bg-ops-card border border-ops-border overflow-hidden shadow-md">
      <div className="p-4 border-b border-ops-border flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Split className="w-4 h-4 text-sky-400" />
          <h2 className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
            Active Deployments & Allocations
          </h2>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          {allocations.length} Active Convoys
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/80 text-[11px] font-mono uppercase text-slate-400 border-b border-ops-border">
            <tr>
              <th className="py-2.5 px-4">Resource / Unit</th>
              <th className="py-2.5 px-4">Agency</th>
              <th className="py-2.5 px-4">Destination</th>
              <th className="py-2.5 px-4">Payload</th>
              <th className="py-2.5 px-4">Status</th>
              <th className="py-2.5 px-4 text-right">ETA</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {allocations.length > 0 ? (
              allocations.map((alloc) => {
                return (
                  <tr
                    key={alloc.id}
                    className="hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="py-3 px-4 font-semibold text-slate-200">
                      <div className="flex items-center space-x-2">
                        <Navigation className="w-3.5 h-3.5 text-sky-400 transform rotate-45" />
                        <span>{alloc.resource?.name || 'Mobilized Unit'}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {alloc.resource?.agency?.name || 'Emergency Services'}
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      <button
                        onClick={() => onSelectZone && onSelectZone(alloc.zone_id)}
                        className="flex items-center space-x-1 hover:text-rose-400 transition-colors text-left"
                      >
                        <MapPin className="w-3 h-3 text-rose-500" />
                        <span className="underline decoration-dotted underline-offset-2 font-medium">
                          {getZoneName(alloc.zone_id)}
                        </span>
                      </button>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      Qty: {alloc.quantity}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={alloc.status} />
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-amber-400">
                      <span className="inline-flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-amber-500/80" />
                        <span>{alloc.eta_minutes ?? 15}m</span>
                      </span>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={6} className="py-6 text-center text-slate-500">
                  No active allocations recorded.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
