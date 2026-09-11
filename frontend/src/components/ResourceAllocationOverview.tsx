import React, { useState, useEffect } from 'react';
import { Package, AlertOctagon, CheckCircle2, ShieldAlert, Sparkles, RefreshCw } from 'lucide-react';
import { apiService } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { ResourceSummaryStats, ResourceInventoryItem } from '../types';

export const ResourceAllocationOverview: React.FC = () => {
  const [summary, setSummary] = useState<ResourceSummaryStats | null>(null);
  const [inventory, setInventory] = useState<ResourceInventoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const { lastMessage } = useWebSocket();

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumData, invData] = await Promise.all([
        apiService.getResourceSummary().catch(() => null),
        apiService.getResourceInventory().catch(() => []),
      ]);
      setSummary(sumData);
      setInventory(invData);
    } catch (e) {
      console.error('Failed to load resource allocation overview:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (!lastMessage) return;
    const { event } = lastMessage;
    if (
      event.startsWith('RESOURCE_') ||
      event === 'SOS_ACTIVATED' ||
      event === 'SIMULATION_TRIGGERED'
    ) {
      loadData();
    }
  }, [lastMessage]);

  const fulfillment = summary?.fulfillment_percentages || {
    FOOD: 100,
    WATER: 100,
    SHELTER: 100,
    MEDICINE: 100,
    RESCUE: 100,
    AMBULANCE: 100,
  };

  const resourceConfigs: Record<string, { label: string; owner: string; unit: string; color: string }> = {
    FOOD: { label: 'Food Kits', owner: 'NGO Relief', unit: 'Kits', color: '#f59e0b' },
    WATER: { label: 'Water Units', owner: 'NGO Relief', unit: 'Units', color: '#0284c7' },
    SHELTER: { label: 'Shelter Spaces', owner: 'NGO Relief', unit: 'Spaces', color: '#8b5cf6' },
    MEDICINE: { label: 'Medicine Kits', owner: 'NGO Relief', unit: 'Kits', color: '#10b981' },
    RESCUE: { label: 'Rescue Squads', owner: 'Fire & Rescue', unit: 'Units', color: '#ef4444' },
    AMBULANCE: { label: 'ICU Ambulances', owner: 'Medical Corp', unit: 'Units', color: '#ec4899' },
  };

  return (
    <div className="bg-[#0c1220] border border-[#1e293b] rounded-xl p-4 md:p-5 space-y-4 shadow-lg relative overflow-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e293b] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
            <Package size={18} />
          </div>
          <div>
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-100 uppercase flex items-center gap-2">
              <span>Multi-Agency Resource Allocation & Inventory Engine</span>
              <span className="bg-sky-500/20 text-sky-300 border border-sky-500/30 text-[10px] px-2 py-0.5 rounded-full font-mono">
                AI TRIAGE DISPATCH
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Tri-level accounting: Citizen Requested vs Recommendation Formula vs Real Inventory Decrement.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="text-xs font-bold text-slate-400 hover:text-sky-400 flex items-center gap-1 transition px-2 py-1 rounded bg-[#070a12] border border-[#1e293b]"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            Sync Stock
          </button>
        </div>
      </div>

      {/* Summary KPI Pills */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
        <div className="bg-[#070a12] border border-[#1e293b] p-2.5 rounded-lg">
          <span className="text-[10px] uppercase font-bold text-slate-500 block">Total Requested</span>
          <span className="text-lg font-black text-slate-200 font-mono">
            {summary?.total_requested ?? 0}
          </span>
        </div>
        <div className="bg-[#070a12] border border-[#1e293b] p-2.5 rounded-lg">
          <span className="text-[10px] uppercase font-bold text-sky-400 block">Allocated</span>
          <span className="text-lg font-black text-sky-400 font-mono">
            {summary?.total_allocated ?? 0}
          </span>
        </div>
        <div className="bg-[#070a12] border border-[#1e293b] p-2.5 rounded-lg">
          <span className="text-[10px] uppercase font-bold text-indigo-400 block">Dispatched</span>
          <span className="text-lg font-black text-indigo-400 font-mono">
            {summary?.total_dispatched ?? 0}
          </span>
        </div>
        <div className="bg-[#070a12] border border-[#1e293b] p-2.5 rounded-lg">
          <span className="text-[10px] uppercase font-bold text-emerald-400 block">Delivered</span>
          <span className="text-lg font-black text-emerald-400 font-mono">
            {summary?.total_delivered ?? 0}
          </span>
        </div>
        <div className={`border p-2.5 rounded-lg col-span-2 sm:col-span-1 ${
          (summary?.total_shortage ?? 0) > 0
            ? 'bg-red-950/20 border-red-500/40'
            : 'bg-[#070a12] border-[#1e293b]'
        }`}>
          <span className="text-[10px] uppercase font-bold text-rose-400 block">Deficit / Shortage</span>
          <span className={`text-lg font-black font-mono ${
            (summary?.total_shortage ?? 0) > 0 ? 'text-rose-400' : 'text-slate-400'
          }`}>
            {summary?.total_shortage ?? 0}
          </span>
        </div>
      </div>

      {/* Fulfillment Progress Bars */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {Object.entries(resourceConfigs).map(([key, cfg]) => {
          const pct = fulfillment[key] ?? 100;
          const inv = inventory.find((i) => i.resource_type === key);
          const avail = inv?.available_quantity ?? 0;
          const total = inv?.total_quantity ?? 0;

          return (
            <div
              key={key}
              className="bg-[#070a12] border border-[#1e293b] rounded-lg p-3 space-y-2 relative overflow-hidden"
            >
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-slate-100">{cfg.label}</span>
                  <span className="text-[10px] text-slate-400 font-mono">({cfg.owner})</span>
                </div>
                <span className="font-mono font-bold text-xs" style={{ color: cfg.color }}>
                  {pct}% Fulfilled
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-[#1e293b] h-2 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.min(100, Math.max(0, pct))}%`,
                    backgroundColor: pct < 50 ? '#ef4444' : pct < 85 ? '#f59e0b' : cfg.color,
                  }}
                />
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                <span>Stock: <strong className="text-slate-200">{avail}</strong> / {total} {cfg.unit}</span>
                <span className={`font-bold ${avail === 0 ? 'text-red-400 animate-pulse' : 'text-emerald-400'}`}>
                  {avail === 0 ? 'DEPLETED' : 'AVAILABLE'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Critical Shortages Banner if any */}
      {summary?.critical_shortages && summary.critical_shortages.length > 0 && (
        <div className="bg-red-950/20 border border-red-500/40 rounded-lg p-3 space-y-2">
          <div className="flex items-center gap-2 text-rose-400 text-xs font-bold font-mono">
            <AlertOctagon size={16} className="animate-bounce" />
            <span>CRITICAL INVENTORY SHORTAGE LOGS ({summary.critical_shortages.length})</span>
          </div>
          <div className="space-y-1.5 max-h-36 overflow-y-auto">
            {summary.critical_shortages.map((sh, idx) => (
              <div
                key={idx}
                className="bg-[#070a12]/80 border border-red-500/20 p-2 rounded text-[11px] flex items-center justify-between font-mono"
              >
                <div>
                  <span className="font-black text-rose-300 mr-2">{sh.incident_id}</span>
                  <span className="text-slate-300">{sh.resource_type}: Requested {sh.requested}, Allocated {sh.allocated}</span>
                </div>
                <span className="text-rose-400 font-bold">Deficit: -{sh.shortage} units</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
