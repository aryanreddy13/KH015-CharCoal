import React, { useState } from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import { StatusBadge } from '../components/StatusBadge';
import { Truck, Search, Filter, ShieldCheck, Navigation } from 'lucide-react';

export const ResourcesPage: React.FC = () => {
  const { resources } = useDashboardData();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');

  const filteredResources = resources.filter((res) => {
    const matchesSearch =
      res.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      res.agency?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      res.resource_type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = selectedType === 'ALL' || res.resource_type.toUpperCase() === selectedType.toUpperCase();
    return matchesSearch && matchesType;
  });

  const resourceTypes = ['ALL', 'Rescue', 'Medical', 'Medicine', 'Food', 'Water', 'Shelter'];

  return (
    <div className="space-y-4 max-w-[1700px] mx-auto pb-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-ops-border pb-3">
        <div>
          <h1 className="text-lg font-bold text-white font-mono flex items-center space-x-2">
            <Truck className="w-5 h-5 text-emerald-400" />
            <span>EMERGENCY RESOURCE INVENTORY</span>
          </h1>
          <p className="text-xs text-slate-400">
            Multi-agency asset directory, availability states, and vehicle capacity.
          </p>
        </div>

        {/* Quick Search & Filter */}
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search resources..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />
          </div>
        </div>
      </div>

      {/* Type Filter Pills */}
      <div className="flex flex-wrap gap-2">
        {resourceTypes.map((type) => (
          <button
            key={type}
            onClick={() => setSelectedType(type)}
            className={`px-3 py-1 rounded-lg text-xs font-mono font-medium transition-colors ${
              selectedType === type
                ? 'bg-rose-600 text-white shadow-sm'
                : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      {/* Resource Table */}
      <div className="rounded-xl bg-ops-card border border-ops-border overflow-hidden shadow-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-[11px] font-mono uppercase text-slate-400 border-b border-ops-border">
              <tr>
                <th className="py-3 px-4">Resource / Asset</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Agency Affiliation</th>
                <th className="py-3 px-4">Quantity / Units</th>
                <th className="py-3 px-4">Capacity / Payload Description</th>
                <th className="py-3 px-4">Base Location</th>
                <th className="py-3 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {filteredResources.length > 0 ? (
                filteredResources.map((res) => (
                  <tr key={res.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-100">
                      <div className="flex items-center space-x-2">
                        <Truck className="w-3.5 h-3.5 text-emerald-400" />
                        <span>{res.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                        {res.resource_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {res.agency?.name || 'Emergency Services'}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-slate-200">
                      {res.quantity}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px] max-w-xs truncate">
                      {res.capacity || 'Standard Emergency Payload'}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                      {res.latitude.toFixed(3)}°N, {res.longitude.toFixed(3)}°E
                    </td>
                    <td className="py-3 px-4 text-right">
                      <StatusBadge status={res.status} />
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No emergency resources found matching criteria.
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
