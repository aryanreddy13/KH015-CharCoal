import React from 'react';
import { Layers, AlertTriangle, Truck, Split, Users } from 'lucide-react';
import { DashboardKPI } from '../types';

interface KpiCardsProps {
  kpi: DashboardKPI;
}

export const KpiCards: React.FC<KpiCardsProps> = ({ kpi }) => {
  const cards = [
    {
      label: 'ACTIVE ZONES',
      value: kpi.active_zones_count,
      sub: '5 Operational Sectors',
      icon: Layers,
      color: 'text-sky-400',
      border: 'border-sky-500/30',
      bg: 'bg-sky-950/20',
    },
    {
      label: 'CRITICAL ZONES',
      value: kpi.critical_zones_count,
      sub: 'Severity > 9.0',
      icon: AlertTriangle,
      color: 'text-rose-400',
      border: 'border-rose-500/40',
      bg: 'bg-rose-950/30',
      pulse: true,
    },
    {
      label: 'AVAILABLE RESOURCES',
      value: kpi.available_resources_count,
      sub: 'Ready for Dispatch',
      icon: Truck,
      color: 'text-emerald-400',
      border: 'border-emerald-500/30',
      bg: 'bg-emerald-950/20',
    },
    {
      label: 'ACTIVE ALLOCATIONS',
      value: kpi.active_allocations_count,
      sub: 'En Route / Mobilized',
      icon: Split,
      color: 'text-amber-400',
      border: 'border-amber-500/30',
      bg: 'bg-amber-950/20',
    },
    {
      label: 'PEOPLE AFFECTED',
      value: kpi.total_people_affected.toLocaleString(),
      sub: 'Across Reported Zones',
      icon: Users,
      color: 'text-indigo-400',
      border: 'border-indigo-500/30',
      bg: 'bg-indigo-950/20',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.label}
            className={`p-3.5 rounded-xl bg-ops-card border ${card.border} ${card.bg} relative overflow-hidden transition-transform hover:-translate-y-0.5 shadow-sm`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono font-semibold tracking-wider text-slate-400">
                {card.label}
              </span>
              <div className={`p-1.5 rounded-lg bg-slate-900/80 ${card.color}`}>
                <Icon className={`w-4 h-4 ${card.pulse ? 'animate-pulse' : ''}`} />
              </div>
            </div>
            <div className="flex items-baseline space-x-2">
              <div className="text-2xl font-black font-mono tracking-tight text-white">
                {card.value}
              </div>
            </div>
            <div className="text-[11px] text-slate-400 mt-1 font-sans truncate">{card.sub}</div>
          </div>
        );
      })}
    </div>
  );
};
