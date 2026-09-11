import React, { useState } from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import { LiveAlertsFeed } from '../components/LiveAlertsFeed';
import { AlertOctagon, Plus, Send, AlertTriangle } from 'lucide-react';
import { apiService } from '../services/api';

export const AlertsPage: React.FC = () => {
  const { alerts, zones, refresh } = useDashboardData();
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [level, setLevel] = useState<'CRITICAL' | 'WARNING' | 'INFO'>('CRITICAL');
  const [zoneId, setZoneId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !message) return;
    try {
      setSubmitting(true);
      await apiService.createAlert({
        title,
        message,
        alert_level: level,
        zone_id: zoneId || undefined,
        is_active: true,
      });
      setTitle('');
      setMessage('');
      setShowForm(false);
      refresh();
    } catch (err) {
      console.error('Failed to create alert:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4 max-w-[1700px] mx-auto pb-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-ops-border pb-3">
        <div>
          <h1 className="text-lg font-bold text-white font-mono flex items-center space-x-2">
            <AlertOctagon className="w-5 h-5 text-rose-500" />
            <span>CRITICAL INCIDENT ALERTS</span>
          </h1>
          <p className="text-xs text-slate-400">
            Real-time threat broadcasts and high-priority operational warnings.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-sm transition-all"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Broadcast New Alert</span>
        </button>
      </div>

      {/* Optional New Alert Drawer */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="p-4 rounded-xl bg-ops-card border border-rose-500/40 space-y-3 shadow-lg"
        >
          <div className="text-xs font-bold text-rose-400 uppercase font-mono">
            Broadcast Emergency Alert to Network
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] text-slate-400 font-mono mb-1">Alert Title</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Critical Medical Shortage"
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 font-mono mb-1">Severity Level</label>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value as any)}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-rose-500"
              >
                <option value="CRITICAL">CRITICAL</option>
                <option value="WARNING">WARNING</option>
                <option value="INFO">INFO</option>
              </select>
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 font-mono mb-1">Related Sector</label>
              <select
                value={zoneId}
                onChange={(e) => setZoneId(e.target.value)}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-rose-500"
              >
                <option value="">All Operational Zones</option>
                {zones.map((z) => (
                  <option key={z.id} value={z.id}>
                    {z.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-[11px] text-slate-400 font-mono mb-1">Alert Message / Instructions</label>
            <textarea
              required
              rows={2}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Provide exact status and instructions..."
              className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />
          </div>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded-lg text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{submitting ? 'Broadcasting...' : 'Broadcast Alert'}</span>
            </button>
          </div>
        </form>
      )}

      {/* Main Alerts Feed */}
      <div className="grid grid-cols-1 gap-4">
        <LiveAlertsFeed alerts={alerts} />
      </div>
    </div>
  );
};
