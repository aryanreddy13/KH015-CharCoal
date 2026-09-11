import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Zone } from '../types';
import { getSeverityColor } from '../utils/formatters';
import { AlertCircle, Flame, Waves, Wind, ShieldAlert } from 'lucide-react';

interface DisasterMapProps {
  zones: Zone[];
  selectedZoneId?: string | null;
  onSelectZone: (zoneId: string) => void;
}

// Custom Leaflet DivIcon with radar pulse and severity badge
function createSeverityMarkerIcon(zone: Zone, isSelected: boolean) {
  let color = '#ef4444'; // Red for Critical
  let glow = 'rgba(239, 68, 68, 0.4)';
  if (zone.overall_severity >= 9.0 || zone.status === 'Critical') {
    color = '#ef4444';
    glow = 'rgba(239, 68, 68, 0.6)';
  } else if (zone.overall_severity >= 7.0 || zone.status === 'High') {
    color = '#f97316';
    glow = 'rgba(249, 115, 22, 0.5)';
  } else if (zone.overall_severity >= 4.0 || zone.status === 'Moderate') {
    color = '#eab308';
    glow = 'rgba(234, 179, 8, 0.5)';
  } else {
    color = '#10b981';
    glow = 'rgba(16, 185, 129, 0.5)';
  }

  const pulseClass = isSelected ? 'scale-125 ring-4 ring-white' : '';

  const html = `
    <div style="position: relative; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;">
      <div style="position: absolute; width: 36px; height: 36px; border-radius: 50%; background-color: ${glow}; animation: ping-slow 2s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
      <div class="${pulseClass}" style="position: relative; width: 26px; height: 26px; border-radius: 50%; background: #111726; border: 2.5px solid ${color}; box-shadow: 0 0 10px ${color}; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 11px; font-family: monospace; color: ${color};">
        ${zone.overall_severity.toFixed(1)}
      </div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-disaster-marker',
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -20],
  });
}

// Controller to smoothly pan to selected zone
const MapController: React.FC<{ selectedZone?: Zone | null }> = ({ selectedZone }) => {
  const map = useMap();
  useEffect(() => {
    if (selectedZone) {
      map.flyTo([selectedZone.latitude, selectedZone.longitude], 12, { duration: 1.2 });
    }
  }, [selectedZone, map]);

  return null;
};

export const DisasterMap: React.FC<DisasterMapProps> = ({ zones, selectedZoneId, onSelectZone }) => {
  // Default map center
  const defaultCenter: [number, number] = [28.6139, 77.2090];
  const selectedZone = zones.find((z) => z.id === selectedZoneId) || null;

  const getDisasterIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'flood':
        return <Waves className="w-4 h-4 text-sky-400 inline mr-1" />;
      case 'earthquake':
        return <AlertCircle className="w-4 h-4 text-amber-400 inline mr-1" />;
      case 'cyclone':
        return <Wind className="w-4 h-4 text-teal-400 inline mr-1" />;
      case 'fire':
        return <Flame className="w-4 h-4 text-rose-400 inline mr-1" />;
      default:
        return <ShieldAlert className="w-4 h-4 text-red-400 inline mr-1" />;
    }
  };

  return (
    <div className="relative w-full h-full min-h-[380px] rounded-xl overflow-hidden border border-ops-border shadow-inner bg-slate-950">
      <MapContainer
        center={defaultCenter}
        zoom={11}
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%', minHeight: '380px' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={import.meta.env.VITE_MAP_TILE_URL || "https://tile.openstreetmap.org/{z}/{x}/{y}.png"}
        />

        <MapController selectedZone={selectedZone} />

        {zones.map((zone) => {
          const isSelected = zone.id === selectedZoneId;
          const icon = createSeverityMarkerIcon(zone, isSelected);
          const sevColor = getSeverityColor(zone.overall_severity);

          return (
            <Marker
              key={zone.id}
              position={[zone.latitude, zone.longitude]}
              icon={icon}
              eventHandlers={{
                click: () => onSelectZone(zone.id),
              }}
            >
              <Popup className="custom-ops-popup">
                <div className="p-1 space-y-2 min-w-[200px]">
                  <div className="flex items-center justify-between border-b border-slate-700 pb-1.5">
                    <span className="font-bold text-slate-100 text-xs truncate max-w-[150px]">
                      {zone.name}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${sevColor.bg} ${sevColor.text} border ${sevColor.border}`}
                    >
                      {zone.status.toUpperCase()}
                    </span>
                  </div>

                  <div className="text-xs space-y-1 text-slate-300">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Hazard:</span>
                      <span className="font-medium flex items-center">
                        {getDisasterIcon(zone.disaster_type)} {zone.disaster_type}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Severity Index:</span>
                      <span className="font-mono font-bold text-rose-400">
                        {zone.overall_severity.toFixed(1)} / 10
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Affected Population:</span>
                      <span className="font-mono font-bold text-slate-200">
                        {zone.affected_people}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => onSelectZone(zone.id)}
                    className="w-full mt-2 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs font-semibold transition-colors shadow-sm"
                  >
                    Inspect Zone Details
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Map Legend Overlay */}
      <div className="absolute top-3 right-3 z-[1000] bg-slate-900/90 backdrop-blur border border-slate-800 rounded-lg p-2.5 shadow-lg space-y-1.5 pointer-events-auto text-[11px] font-mono">
        <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
          Severity Level
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.8)]" />
          <span className="text-slate-300">Critical (9.0 - 10.0)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
          <span className="text-slate-300">High (7.0 - 8.9)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
          <span className="text-slate-300">Moderate (4.0 - 6.9)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          <span className="text-slate-300">Low (0.0 - 3.9)</span>
        </div>
      </div>
    </div>
  );
};
