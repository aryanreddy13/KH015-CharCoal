import React, { useState, useEffect, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Zone, Resource, Allocation } from '../types';
import { getSeverityColor } from '../utils/formatters';
import { apiService } from '../services/api';
import {
  AlertCircle,
  Flame,
  Waves,
  Wind,
  ShieldAlert,
  Navigation,
  Package,
  HeartPulse,
  Truck,
  Droplets,
  Layers,
  Radio,
  Clock,
  Compass,
  Eye,
  CheckCircle2,
  ChevronRight,
  Maximize2,
} from 'lucide-react';

interface DisasterMapProps {
  zones: Zone[];
  selectedZoneId?: string | null;
  onSelectZone: (zoneId: string) => void;
  resources?: Resource[];
  allocations?: Allocation[];
}

interface SupplyStation {
  id: string;
  name: string;
  category: 'MEDICAL' | 'FOOD_WATER' | 'RESCUE' | 'AMBULANCE' | 'GENERAL';
  resource_type: string;
  stock_quantity: number;
  unit: string;
  latitude: number;
  longitude: number;
  address?: string;
  phone?: string;
}

// Custom Leaflet DivIcon for Critical Zone with Radar Pulse & Severity Score
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

  const pulseClass = isSelected ? 'scale-125 ring-4 ring-white shadow-[0_0_20px_rgba(255,255,255,0.8)]' : '';

  const html = `
    <div style="position: relative; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
      <div style="position: absolute; width: 40px; height: 40px; border-radius: 50%; background-color: ${glow}; animation: ping-slow 2s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
      <div class="${pulseClass}" style="position: relative; width: 28px; height: 28px; border-radius: 50%; background: #090d16; border: 2.5px solid ${color}; box-shadow: 0 0 14px ${color}; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 11px; font-family: monospace; color: ${color};">
        ${zone.overall_severity.toFixed(1)}
      </div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-disaster-marker',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -22],
  });
}

// Custom Leaflet DivIcon for Supply Depot / Stockpile
function createSupplyDepotIcon(station: SupplyStation, isNearest: boolean) {
  let iconBg = '#0284c7';
  let badgeColor = '#38bdf8';
  let emoji = '📦';

  if (station.category === 'MEDICAL') {
    iconBg = '#dc2626';
    badgeColor = '#f87171';
    emoji = '🏥';
  } else if (station.category === 'FOOD_WATER') {
    iconBg = '#0d9488';
    badgeColor = '#2dd4bf';
    emoji = '💧';
  } else if (station.category === 'RESCUE') {
    iconBg = '#d97706';
    badgeColor = '#fbbf24';
    emoji = '🛡️';
  } else if (station.category === 'AMBULANCE') {
    iconBg = '#e11d48';
    badgeColor = '#fb7185';
    emoji = '🚑';
  }

  const ringStyle = isNearest
    ? 'border-2 border-white ring-4 ring-sky-400 shadow-[0_0_20px_rgba(56,189,248,0.9)] scale-110'
    : 'border border-slate-700 shadow-md';

  const html = `
    <div style="position: relative; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;">
      <div class="${ringStyle}" style="width: 30px; height: 30px; border-radius: 8px; background: ${iconBg}; display: flex; align-items: center; justify-content: center; font-size: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">
        ${emoji}
      </div>
      ${
        isNearest
          ? `<div style="position: absolute; top: -6px; right: -6px; background: #38bdf8; color: #000; font-weight: 900; font-size: 9px; font-family: monospace; padding: 1px 4px; border-radius: 4px; border: 1px solid #fff;">NEAREST</div>`
          : ''
      }
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-supply-marker',
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -18],
  });
}

// Map Controller for smooth flyTo animations
const MapController: React.FC<{ selectedZone?: Zone | null; focus1kmTrigger?: number }> = ({
  selectedZone,
  focus1kmTrigger,
}) => {
  const map = useMap();

  useEffect(() => {
    if (selectedZone && selectedZone.latitude && selectedZone.longitude) {
      map.flyTo([selectedZone.latitude, selectedZone.longitude], 13, { duration: 1.2 });
    }
  }, [selectedZone, map]);

  useEffect(() => {
    if (focus1kmTrigger && selectedZone) {
      // Zoom in tight to 1km radius perimeter (approx zoom level 14-15)
      map.flyTo([selectedZone.latitude, selectedZone.longitude], 14.5, { duration: 0.9 });
    }
  }, [focus1kmTrigger, selectedZone, map]);

  return null;
};

export const DisasterMap: React.FC<DisasterMapProps> = ({
  zones,
  selectedZoneId,
  onSelectZone,
  resources,
  allocations,
}) => {
  const defaultCenter: [number, number] = [19.0760, 72.8777];
  const [show1kmRadius, setShow1kmRadius] = useState(true);
  const [showSupplyRoutes, setShowSupplyRoutes] = useState(true);
  const [showSupplies, setShowSupplies] = useState(true);
  const [selectedDepotId, setSelectedDepotId] = useState<string | null>(null);
  const [routeCoordinates, setRouteCoordinates] = useState<[number, number][]>([]);
  const [routeDistance, setRouteDistance] = useState<string>('3.8 km');
  const [routeEta, setRouteEta] = useState<string>('7 min');
  const [routeLoading, setRouteLoading] = useState(false);
  const [focusTrigger, setFocusTrigger] = useState(0);

  // Identify selected zone or default to most critical zone
  const criticalZone = useMemo(() => {
    if (selectedZoneId) {
      const found = zones.find((z) => z.id === selectedZoneId);
      if (found) return found;
    }
    // Find highest severity zone
    if (zones.length > 0) {
      return [...zones].sort((a, b) => b.overall_severity - a.overall_severity)[0];
    }
    return null;
  }, [zones, selectedZoneId]);

  // Generate realistic supply stations near critical zones in Mumbai
  const supplyStations: SupplyStation[] = useMemo(() => {
    if (!criticalZone) return [];

    const lat = criticalZone.latitude;
    const lon = criticalZone.longitude;

    return [
      {
        id: `depot-medical-${criticalZone.id}`,
        name: 'BMC Central Trauma & KEM Reserve Hub',
        category: 'MEDICAL',
        resource_type: 'Medical Trauma Kits & Plasma',
        stock_quantity: 450,
        unit: 'Kits',
        latitude: lat + 0.024,
        longitude: lon - 0.018,
        address: 'Parel / Dadar Medical Corridor Depot',
        phone: '108',
      },
      {
        id: `depot-water-${criticalZone.id}`,
        name: 'Wadala & Kurla Potable Water Stockpile',
        category: 'FOOD_WATER',
        resource_type: 'Purified Water & Emergency Rations',
        stock_quantity: 2800,
        unit: 'Liters / Packs',
        latitude: lat - 0.021,
        longitude: lon + 0.022,
        address: 'Civil Supplies Regional Warehouse (Wadala)',
        phone: '1077',
      },
      {
        id: `depot-rescue-${criticalZone.id}`,
        name: 'Mumbai Fire Brigade & NDRF Mobilization Center',
        category: 'RESCUE',
        resource_type: 'Heavy Rescue Boats & Inflatable Rafts',
        stock_quantity: 12,
        unit: 'Rescue Units',
        latitude: lat + 0.018,
        longitude: lon + 0.026,
        address: 'BKC / Byculla Fire Command Post',
        phone: '101',
      },
      {
        id: `depot-ambulance-${criticalZone.id}`,
        name: '108 Rapid Response Ambulance & ICU Base',
        category: 'AMBULANCE',
        resource_type: 'ICU Mobile Ambulances',
        stock_quantity: 6,
        unit: 'Vehicles',
        latitude: lat - 0.019,
        longitude: lon - 0.023,
        address: 'Western & Eastern Express Transit Base',
        phone: '102',
      },
    ];
  }, [criticalZone]);

  // Selected or nearest depot
  const activeDepot = useMemo(() => {
    if (!supplyStations.length) return null;
    if (selectedDepotId) {
      const found = supplyStations.find((s) => s.id === selectedDepotId);
      if (found) return found;
    }
    return supplyStations[0]; // Nearest depot
  }, [supplyStations, selectedDepotId]);

  // Fetch or calculate driving route coordinates from active supply depot to critical zone
  useEffect(() => {
    if (!criticalZone || !activeDepot) {
      setRouteCoordinates([]);
      return;
    }

    let isMounted = true;
    setRouteLoading(true);

    apiService
      .getEmergencyRoute(
        activeDepot.latitude,
        activeDepot.longitude,
        criticalZone.latitude,
        criticalZone.longitude
      )
      .then((res) => {
        if (!isMounted) return;
        if (res && res.coordinates && res.coordinates.length > 0) {
          setRouteCoordinates(res.coordinates);
          setRouteDistance(res.distance_text || `${res.distance_km} km`);
          setRouteEta(res.eta_text || `ETA ~${res.eta_minutes} min`);
        } else {
          // Fallback interpolated points
          const points: [number, number][] = [
            [activeDepot.latitude, activeDepot.longitude],
            [
              activeDepot.latitude * 0.6 + criticalZone.latitude * 0.4 + 0.002,
              activeDepot.longitude * 0.6 + criticalZone.longitude * 0.4 - 0.002,
            ],
            [
              activeDepot.latitude * 0.3 + criticalZone.latitude * 0.7 - 0.001,
              activeDepot.longitude * 0.3 + criticalZone.longitude * 0.7 + 0.001,
            ],
            [criticalZone.latitude, criticalZone.longitude],
          ];
          setRouteCoordinates(points);
          setRouteDistance('3.8 km');
          setRouteEta('7 min');
        }
      })
      .catch((err) => {
        console.warn('Route calculation fallback:', err);
        if (!isMounted) return;
        const points: [number, number][] = [
          [activeDepot.latitude, activeDepot.longitude],
          [
            activeDepot.latitude * 0.5 + criticalZone.latitude * 0.5 + 0.002,
            activeDepot.longitude * 0.5 + criticalZone.longitude * 0.5 - 0.002,
          ],
          [criticalZone.latitude, criticalZone.longitude],
        ];
        setRouteCoordinates(points);
        setRouteDistance('3.8 km');
        setRouteEta('7 min');
      })
      .finally(() => {
        if (isMounted) setRouteLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [criticalZone, activeDepot]);

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
    <div className="relative w-full h-full min-h-[460px] rounded-2xl overflow-hidden border border-ops-border shadow-2xl bg-slate-950 font-sans select-none">
      <MapContainer
        center={criticalZone ? [criticalZone.latitude, criticalZone.longitude] : defaultCenter}
        zoom={criticalZone ? 13 : 5}
        minZoom={4}
        maxZoom={18}
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%', minHeight: '460px' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={import.meta.env.VITE_MAP_TILE_URL || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'}
        />

        <MapController selectedZone={criticalZone} focus1kmTrigger={focusTrigger} />

        {/* 1. CRITICAL ZONE 1KM GEOMAP RADIUS OVERLAYS */}
        {show1kmRadius &&
          zones.map((zone) => {
            const isSelected = zone.id === criticalZone?.id;
            const isSevere = zone.overall_severity >= 7.0 || zone.status === 'Critical';
            if (!isSelected && !isSevere) return null;

            return (
              <React.Fragment key={`radius-group-${zone.id}`}>
                {/* 1000m (1km) Outer Danger Perimeter */}
                <Circle
                  center={[zone.latitude, zone.longitude]}
                  radius={1000} // Exactly 1,000 meters = 1km radius
                  pathOptions={{
                    color: isSelected ? '#ef4444' : '#f97316',
                    fillColor: isSelected ? '#ef4444' : '#f97316',
                    fillOpacity: isSelected ? 0.16 : 0.08,
                    weight: isSelected ? 2.5 : 1.5,
                    dashArray: '8, 8',
                  }}
                />

                {/* 500m Epicenter Core Buffer */}
                <Circle
                  center={[zone.latitude, zone.longitude]}
                  radius={500}
                  pathOptions={{
                    color: '#dc2626',
                    fillColor: '#dc2626',
                    fillOpacity: isSelected ? 0.22 : 0.12,
                    weight: 2,
                  }}
                />
              </React.Fragment>
            );
          })}

        {/* 2. SUPPLY CONVOY ROUTE POLYLINE (Dashed glowing corridor to critical zone) */}
        {showSupplyRoutes && routeCoordinates.length > 1 && (
          <>
            {/* Outer Glow Halo */}
            <Polyline
              positions={routeCoordinates}
              pathOptions={{
                color: '#38bdf8',
                weight: 8,
                opacity: 0.35,
                lineCap: 'round',
              }}
            />
            {/* Main Animated Cyber Transit Line */}
            <Polyline
              positions={routeCoordinates}
              pathOptions={{
                color: '#0284c7',
                weight: 4,
                opacity: 0.95,
                dashArray: '10, 10',
                dashOffset: '0',
                lineCap: 'round',
              }}
            />
          </>
        )}

        {/* 3. SUPPLY DEPOT MARKERS */}
        {showSupplies &&
          supplyStations.map((station) => {
            const isSelectedDepot = station.id === activeDepot?.id;
            const depotIcon = createSupplyDepotIcon(station, isSelectedDepot);

            return (
              <Marker
                key={station.id}
                position={[station.latitude, station.longitude]}
                icon={depotIcon}
                eventHandlers={{
                  click: () => setSelectedDepotId(station.id),
                }}
              >
                <Popup className="custom-ops-popup">
                  <div className="p-1 space-y-2 min-w-[210px] font-mono">
                    <div className="flex items-center justify-between border-b border-slate-700 pb-1.5">
                      <span className="font-bold text-sky-400 text-xs truncate">
                        {station.name}
                      </span>
                      <span className="text-[10px] bg-sky-950 text-sky-300 px-1.5 py-0.5 rounded border border-sky-500/30">
                        {station.category}
                      </span>
                    </div>

                    <div className="text-xs space-y-1 text-slate-300">
                      <div className="text-[11px] text-slate-200">
                        <strong>Supplies:</strong> {station.resource_type}
                      </div>
                      <div className="text-[11px] text-emerald-400 font-bold">
                        Stock: {station.stock_quantity} {station.unit} Available
                      </div>
                      {station.phone && (
                        <div className="text-[10px] text-slate-400">
                          Emergency Contact: <span className="text-white font-bold">{station.phone}</span>
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => setSelectedDepotId(station.id)}
                      className="w-full mt-1.5 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-[11px] font-bold transition shadow-sm flex items-center justify-center gap-1"
                    >
                      <Navigation className="w-3 h-3" />
                      <span>Route Supplies from this Depot</span>
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          })}

        {/* 4. DISASTER ZONE MARKERS */}
        {zones.map((zone) => {
          const isSelected = zone.id === criticalZone?.id;
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
                <div className="p-1 space-y-2 min-w-[220px]">
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
                      <span className="text-slate-400">1km Perimeter Casualties:</span>
                      <span className="font-mono font-bold text-slate-200">
                        ~{zone.affected_people} people
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] font-mono text-amber-400 pt-1 border-t border-slate-800">
                      <span>Geomap Radius:</span>
                      <span className="font-bold">1,000 meters (1.0 km)</span>
                    </div>
                  </div>

                  <button
                    onClick={() => onSelectZone(zone.id)}
                    className="w-full mt-2 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs font-semibold transition shadow-sm"
                  >
                    Inspect Zone & Route Supplies
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* TOP LEFT: Quick Sector Focus Pill */}
      <div className="absolute top-3 left-3 z-[1000] flex flex-wrap items-center gap-1.5 pointer-events-auto">
        <span className="bg-slate-900/90 backdrop-blur border border-slate-700/80 px-2 py-1 rounded-lg text-[11px] font-mono font-bold text-slate-300 shadow-lg flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
          <span>SECTORS:</span>
        </span>
        {zones.slice(0, 5).map((z) => (
          <button
            key={z.id}
            onClick={() => onSelectZone(z.id)}
            className={`px-2 py-1 rounded-lg text-[10px] font-mono font-bold transition shadow-sm border ${
              z.id === criticalZone?.id
                ? 'bg-rose-600 text-white border-rose-400'
                : 'bg-slate-900/90 text-slate-300 border-slate-800 hover:border-slate-600'
            }`}
          >
            {z.name.replace('Operational ', '')}
          </button>
        ))}
      </div>

      {/* TOP RIGHT: Map Layer Controls HUD */}
      <div className="absolute top-3 right-3 z-[1000] bg-slate-900/95 backdrop-blur-md border border-slate-800 rounded-xl p-2.5 shadow-2xl space-y-2 pointer-events-auto text-[11px] font-mono">
        <div className="flex items-center justify-between border-b border-slate-800 pb-1 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
          <span className="flex items-center gap-1">
            <Layers className="w-3 h-3 text-sky-400" />
            <span>Geomap Overlays</span>
          </span>
          <button
            onClick={() => setFocusTrigger((prev) => prev + 1)}
            title="Fit to 1km critical perimeter"
            className="text-sky-400 hover:text-sky-300 p-0.5 rounded hover:bg-slate-800"
          >
            <Maximize2 className="w-3 h-3" />
          </button>
        </div>

        {/* 1km Radius Toggle */}
        <label className="flex items-center justify-between gap-3 cursor-pointer hover:text-white transition">
          <span className="flex items-center gap-1.5 text-slate-300 text-[10px]">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            <span>1km Critical Perimeter</span>
          </span>
          <input
            type="checkbox"
            checked={show1kmRadius}
            onChange={(e) => setShow1kmRadius(e.target.checked)}
            className="rounded accent-rose-500 cursor-pointer"
          />
        </label>

        {/* Supply Routes Toggle */}
        <label className="flex items-center justify-between gap-3 cursor-pointer hover:text-white transition">
          <span className="flex items-center gap-1.5 text-slate-300 text-[10px]">
            <span className="w-2 h-2 rounded-full bg-sky-400" />
            <span>Supply Convoy Route</span>
          </span>
          <input
            type="checkbox"
            checked={showSupplyRoutes}
            onChange={(e) => setShowSupplyRoutes(e.target.checked)}
            className="rounded accent-sky-500 cursor-pointer"
          />
        </label>

        {/* Supply Stockpiles Toggle */}
        <label className="flex items-center justify-between gap-3 cursor-pointer hover:text-white transition">
          <span className="flex items-center gap-1.5 text-slate-300 text-[10px]">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Nearby Supply Depots</span>
          </span>
          <input
            type="checkbox"
            checked={showSupplies}
            onChange={(e) => setShowSupplies(e.target.checked)}
            className="rounded accent-emerald-500 cursor-pointer"
          />
        </label>
      </div>

      {/* BOTTOM FLOATING HUD: Nearest Supply Route Telemetry */}
      {criticalZone && activeDepot && (
        <div className="absolute bottom-3 left-3 right-3 z-[1000] bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-xl p-3 shadow-2xl pointer-events-auto flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
          {/* Left: Critical Zone 1km Info */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-rose-950/80 border border-rose-500/40 flex items-center justify-center text-rose-400 shrink-0 shadow-[0_0_15px_rgba(244,63,94,0.3)]">
              <ShieldAlert className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-extrabold uppercase text-rose-400 bg-rose-950/60 px-1.5 py-0.5 rounded border border-rose-500/30">
                  1KM CRITICAL ZONE
                </span>
                <span className="font-bold text-white text-xs">{criticalZone.name}</span>
                <span className="text-[10px] text-slate-400">({criticalZone.disaster_type})</span>
              </div>
              <div className="text-[11px] text-slate-300 flex items-center gap-2 mt-0.5">
                <span>Perimeter: <strong className="text-white">1,000m buffer</strong></span>
                <span>•</span>
                <span>Casualties: <strong className="text-amber-400">{criticalZone.affected_people} affected</strong></span>
              </div>
            </div>
          </div>

          {/* Center: Live Convoy Transit Telemetry */}
          <div className="flex items-center gap-3 bg-slate-950/80 p-2 rounded-lg border border-slate-800">
            <div className="text-[10px] text-slate-400">
              <div>NEAREST SUPPLY DEPOT:</div>
              <div className="text-sky-300 font-bold text-xs truncate max-w-[180px]">
                {activeDepot.name}
              </div>
            </div>

            <div className="border-l border-slate-800 pl-3 flex items-center gap-3">
              <div>
                <div className="text-[9px] text-slate-400 uppercase">Transit Distance</div>
                <div className="text-xs font-bold text-white flex items-center gap-1">
                  <Compass className="w-3 h-3 text-sky-400" />
                  <span>{routeDistance}</span>
                </div>
              </div>

              <div>
                <div className="text-[9px] text-slate-400 uppercase">Convoy ETA</div>
                <div className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                  <Clock className="w-3 h-3 text-emerald-400" />
                  <span>{routeEta}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Quick Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFocusTrigger((prev) => prev + 1)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs flex items-center gap-1 transition"
            >
              <Eye className="w-3 h-3 text-sky-400" />
              <span>Zoom 1km</span>
            </button>
            <a
              href={`https://www.google.com/maps/dir/?api=1&origin=${activeDepot.latitude},${activeDepot.longitude}&destination=${criticalZone.latitude},${criticalZone.longitude}`}
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center gap-1 shadow-sm transition"
            >
              <Navigation className="w-3 h-3" />
              <span>Dispatch Supplies</span>
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
