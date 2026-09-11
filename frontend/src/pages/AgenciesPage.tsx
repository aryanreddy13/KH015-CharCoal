import React, { useState, useEffect } from 'react';
import { Agency } from '../types';
import { apiService } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { Building2, Phone, ShieldCheck, Truck, Users } from 'lucide-react';

export const AgenciesPage: React.FC = () => {
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiService
      .getAgencies()
      .then(setAgencies)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4 max-w-[1700px] mx-auto pb-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-ops-border pb-3">
        <div>
          <h1 className="text-lg font-bold text-white font-mono flex items-center space-x-2">
            <Building2 className="w-5 h-5 text-indigo-400" />
            <span>PARTICIPATING EMERGENCY AGENCIES</span>
          </h1>
          <p className="text-xs text-slate-400">
            Government authorities, emergency responder squads, and partner NGOs.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-300 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          Agencies: <span className="text-sky-400 font-bold">{agencies.length}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agencies.map((agency) => (
          <div
            key={agency.id}
            className="p-5 rounded-xl bg-ops-card border border-ops-border space-y-3 shadow-md"
          >
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-bold text-sm text-white">{agency.name}</h2>
                <div className="text-xs font-mono text-slate-400">{agency.type}</div>
              </div>
              <StatusBadge status={agency.status} />
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-800 text-xs text-slate-300">
              <div className="flex items-center space-x-2 text-slate-400">
                <Phone className="w-3.5 h-3.5 text-sky-400" />
                <span className="font-mono">{agency.contact_number || '+91-100-555-0199'}</span>
              </div>
              <div className="flex items-center space-x-2 text-slate-400">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Verified First Responder Organization</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
