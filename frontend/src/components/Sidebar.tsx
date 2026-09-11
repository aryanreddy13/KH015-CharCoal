import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  MapPin,
  FileSpreadsheet,
  Layers,
  Truck,
  Split,
  Building2,
  AlertOctagon,
  History,
  Radio,
  ExternalLink,
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Overview', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Live Map', path: '/zones', icon: MapPin },
  { name: 'Reports', path: '/reports', icon: FileSpreadsheet },
  { name: 'Zones', path: '/zones', icon: Layers },
  { name: 'Resources', path: '/resources', icon: Truck },
  { name: 'Allocations', path: '/allocations', icon: Split },
  { name: 'Agencies', path: '/agencies', icon: Building2 },
  { name: 'Alerts', path: '/alerts', icon: AlertOctagon },
  { name: 'Audit Log', path: '/audit', icon: History },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-60 bg-ops-surface border-r border-ops-border flex flex-col justify-between select-none">
      <div className="py-4">
        <div className="px-5 mb-3 text-[11px] font-mono uppercase tracking-wider text-slate-400">
          Navigation Modules
        </div>
        <nav className="space-y-1 px-3">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30 shadow-[0_0_12px_rgba(244,63,94,0.15)]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Bottom Citizen Portal CTA */}
      <div className="p-4 border-t border-ops-border">
        <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-semibold text-rose-400">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>Field Reporter App</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Lightweight mobile interface for citizens and rescue spotters.
          </p>
          <NavLink
            to="/report"
            target="_blank"
            className="flex items-center justify-between w-full px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            <span>Open Reporter</span>
            <ExternalLink className="w-3 h-3" />
          </NavLink>
        </div>
      </div>
    </aside>
  );
};
