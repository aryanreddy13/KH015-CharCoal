import React, { useState } from 'react';
import { Play, AlertOctagon, Construction, Loader2, CheckCircle2 } from 'lucide-react';
import { apiService } from '../services/api';

interface SimulationControlsProps {
  onTriggerSuccess?: () => void;
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({ onTriggerSuccess }) => {
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(
    null
  );

  const handleAction = async (
    action: 'start' | 'emergency' | 'road-block',
    fn: () => Promise<any>
  ) => {
    try {
      setActiveAction(action);
      setFeedback(null);
      const res = await fn();
      setFeedback({
        message: res.message || 'Action executed successfully',
        type: 'success',
      });
      if (onTriggerSuccess) {
        onTriggerSuccess();
      }
      setTimeout(() => setFeedback(null), 4000);
    } catch (err: any) {
      setFeedback({
        message: err.message || 'Simulation action failed',
        type: 'error',
      });
    } finally {
      setActiveAction(null);
    }
  };

  return (
    <div className="p-4 rounded-xl bg-ops-card border border-ops-border shadow-md space-y-3">
      <div className="flex items-center justify-between border-b border-ops-border pb-2.5">
        <div className="flex items-center space-x-2">
          <Play className="w-4 h-4 text-emerald-400" />
          <h2 className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
            Agentic Simulation Scenarios
          </h2>
        </div>
        <span className="text-[11px] font-mono text-slate-400">Phase 1 Trigger Harness</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Start Simulation */}
        <button
          onClick={() => handleAction('start', apiService.startSimulation)}
          disabled={activeAction !== null}
          className="flex items-center justify-center space-x-2 px-3.5 py-2.5 rounded-lg bg-emerald-950/80 hover:bg-emerald-900/90 text-emerald-300 border border-emerald-500/40 text-xs font-semibold shadow-[0_0_12px_rgba(16,185,129,0.2)] transition-all disabled:opacity-50"
        >
          {activeAction === 'start' ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5 text-emerald-400" />
          )}
          <span>START SIMULATION</span>
        </button>

        {/* Inject Emergency */}
        <button
          onClick={() => handleAction('emergency', () => apiService.injectEmergency())}
          disabled={activeAction !== null}
          className="flex items-center justify-center space-x-2 px-3.5 py-2.5 rounded-lg bg-rose-950/80 hover:bg-rose-900/90 text-rose-300 border border-rose-500/50 text-xs font-semibold shadow-[0_0_12px_rgba(239,68,68,0.2)] transition-all disabled:opacity-50"
        >
          {activeAction === 'emergency' ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
          )}
          <span>INJECT EMERGENCY</span>
        </button>

        {/* Simulate Road Block */}
        <button
          onClick={() => handleAction('road-block', apiService.simulateRoadBlock)}
          disabled={activeAction !== null}
          className="flex items-center justify-center space-x-2 px-3.5 py-2.5 rounded-lg bg-amber-950/80 hover:bg-amber-900/90 text-amber-300 border border-amber-500/40 text-xs font-semibold shadow-[0_0_12px_rgba(245,158,11,0.2)] transition-all disabled:opacity-50"
        >
          {activeAction === 'road-block' ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Construction className="w-3.5 h-3.5 text-amber-400" />
          )}
          <span>SIMULATE ROAD BLOCK</span>
        </button>
      </div>

      {feedback && (
        <div
          className={`p-2.5 rounded-lg text-xs flex items-center space-x-2 font-mono ${
            feedback.type === 'success'
              ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
              : 'bg-rose-950/60 text-rose-300 border border-rose-500/30'
          }`}
        >
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{feedback.message}</span>
        </div>
      )}
    </div>
  );
};
