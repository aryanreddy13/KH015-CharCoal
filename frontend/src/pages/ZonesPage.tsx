import React, { useState } from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import { DisasterMap } from '../components/DisasterMap';
import { ZoneDetailsDrawer } from '../components/ZoneDetailsDrawer';
import { getSeverityColor } from '../utils/formatters';
import { Layers, Users, MapPin, Activity, Radio } from 'lucide-react';

export const ZonesPage: React.FC = () => {
  const { zones, allocations, selectedZone, selectedZoneId, setSelectedZoneId } = useDashboardData();

  return (
    <div className="space-y-4 max-w-[1700px] mx-auto pb-8">
      <div className="flex items-center justify-between border-b border-ops-border pb-3">
        <div>
          <h1 className="text-lg font-bold text-white font-mono flex items-center space-x-2">
            <Layers className="w-5 h-5 text-sky-400" />
            <span>DISASTER OPERATIONAL ZONES</span>
          </h1>
          <p className="text-xs text-slate-400">
            Real-time geospatial tracking and severity classification for all 5 sectors.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-300 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          Total Sectors: <span className="text-rose-400 font-bold">{zones.length}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left: Map */}
        <div className="lg:col-span-8 h-[520px]">
          <DisasterMap
            zones={zones}
            selectedZoneId={selectedZoneId}
            onSelectZone={setSelectedZoneId}
          />
        </div>

        {/* Right: Selected Zone Inspector */}
        <div className="lg:col-span-4 h-[520px] overflow-y-auto">
          <ZoneDetailsDrawer zone={selectedZone} allocations={allocations} />
        </div>
      </div>

      {/* Grid of Zone Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3.5">
        {zones.map((zone) => {
          const sevColor = getSeverityColor(zone.overall_severity);
          const isSelected = zone.id === selectedZoneId;

          return (
            <div
              key={zone.id}
              onClick={() => setSelectedZoneId(zone.id)}
              className={`p-4 rounded-xl bg-ops-card border cursor-pointer transition-all duration-150 space-y-3 ${
                isSelected
                  ? 'border-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.2)] bg-slate-900/90'
                  : 'border-ops-border hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-bold text-sm text-white">{zone.name}</h3>
                  <div className="text-xs text-slate-400">{zone.disaster_type}</div>
                </div>
                <span
                  className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${sevColor.bg} ${sevColor.text} ${sevColor.border}`}
                >
                  {zone.overall_severity.toFixed(1)}
                </span>
              </div>

              <div className="space-y-1.5 text-xs text-slate-300">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 flex items-center space-x-1">
                    <Users className="w-3.5 h-3.5" />
                    <span>Casualties / Affected:</span>
                  </span>
                  <span className="font-mono font-bold text-slate-200">
                    {zone.affected_people}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 flex items-center space-x-1">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>GPS Coordinates:</span>
                  </span>
                  <span className="font-mono text-[11px] text-slate-400">
                    {zone.latitude.toFixed(2)}°, {zone.longitude.toFixed(2)}°
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <div className="text-[11px] font-mono text-slate-400 mb-1">Active Needs:</div>
                <div className="flex flex-wrap gap-1">
                  {zone.needs?.map((n) => (
                    <span
                      key={n.id}
                      className="px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 text-[10px] font-mono border border-slate-800"
                    >
                      {n.resource_type} ({n.severity})
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
