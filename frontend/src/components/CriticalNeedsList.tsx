import React from 'react';
import { Zone } from '../types';
import { getSeverityColor } from '../utils/formatters';
import { Activity, Flame, HeartPulse, LifeBuoy, Utensils, Home, Droplets } from 'lucide-react';

interface CriticalNeedsListProps {
  zones: Zone[];
  onSelectZone: (zoneId: string) => void;
}

export const CriticalNeedsList: React.FC<CriticalNeedsListProps> = ({ zones, onSelectZone }) => {
  const getResourceIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'rescue':
        return <LifeBuoy className="w-3.5 h-3.5 text-rose-400" />;
      case 'medical':
      case 'medicine':
        return <HeartPulse className="w-3.5 h-3.5 text-rose-400" />;
      case 'food':
        return <Utensils className="w-3.5 h-3.5 text-amber-400" />;
      case 'water':
        return <Droplets className="w-3.5 h-3.5 text-sky-400" />;
      case 'shelter':
        return <Home className="w-3.5 h-3.5 text-teal-400" />;
      default:
        return <Activity className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="p-4 rounded-xl bg-ops-card border border-ops-border space-y-3 shadow-md">
      <div className="flex items-center justify-between border-b border-ops-border pb-2.5">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-rose-500" />
          <h2 className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
            Critical Needs Manifest
          </h2>
        </div>
        <span className="text-[11px] font-mono text-slate-400">By Sector Hierarchy</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
        {zones.map((zone) => {
          const zoneSev = getSeverityColor(zone.overall_severity);
          return (
            <div
              key={zone.id}
              onClick={() => onSelectZone(zone.id)}
              className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-rose-500/40 cursor-pointer transition-all duration-150 space-y-2.5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-white truncate max-w-[110px]">
                    {zone.name.split(' - ')[0]}
                  </span>
                  <span
                    className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${zoneSev.bg} ${zoneSev.text} ${zoneSev.border}`}
                  >
                    {zone.overall_severity.toFixed(1)}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 truncate">{zone.disaster_type}</div>
              </div>

              {/* Individual Needs List */}
              <div className="space-y-1.5 pt-1 border-t border-slate-800/80">
                {zone.needs && zone.needs.length > 0 ? (
                  zone.needs.map((need) => {
                    const needColor = getSeverityColor(need.severity);
                    return (
                      <div
                        key={need.id}
                        className="flex items-center justify-between text-xs py-0.5"
                      >
                        <span className="flex items-center space-x-1.5 text-slate-300">
                          {getResourceIcon(need.resource_type)}
                          <span className="text-[11px] font-medium">{need.resource_type}</span>
                        </span>
                        <span
                          className={`font-mono text-[11px] font-bold ${needColor.text}`}
                        >
                          {need.severity.toFixed(1)}
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-[11px] text-slate-500 italic">No needs recorded</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
