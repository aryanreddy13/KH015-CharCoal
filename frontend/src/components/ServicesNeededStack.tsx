import React, { useMemo } from 'react';
import {
  LifeBuoy,
  HeartPulse,
  Truck,
  Droplets,
  Utensils,
  Home,
  Shield,
  Layers,
  AlertCircle,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import { Report } from '../types';

export interface ServiceStackItem {
  id: string;
  category: 'RESCUE' | 'MEDICAL' | 'AMBULANCE' | 'FOOD' | 'WATER' | 'SHELTER' | 'POLICE';
  label: string;
  detail: string;
  quantity?: string;
  isUrgent?: boolean;
  color: string;
  bgColor: string;
  borderColor: string;
  icon: React.ElementType;
}

interface ServicesNeededStackProps {
  report: Report;
  variant?: 'compact' | 'full' | 'inline';
}

export function extractNeededServices(report: Report): ServiceStackItem[] {
  const items: ServiceStackItem[] = [];
  const text = (report.description || '').toLowerCase();
  const dType = (report.disaster_type || '').toLowerCase();

  const assessment = report.assessment || {};
  const needsDict = assessment.needs || {};
  const explicitRequests = assessment.explicit_requests || [];

  // Helper to add unique service
  const addService = (
    category: ServiceStackItem['category'],
    label: string,
    defaultDetail: string,
    color: string,
    bgColor: string,
    borderColor: string,
    icon: React.ElementType,
    qtyOverride?: string,
    isUrgent = false
  ) => {
    if (!items.find((i) => i.category === category)) {
      items.push({
        id: `${report.id}-${category}`,
        category,
        label,
        detail: qtyOverride || defaultDetail,
        quantity: qtyOverride,
        isUrgent,
        color,
        bgColor,
        borderColor,
        icon,
      });
    }
  };

  // 1. Check Explicit Requests from AI Extraction
  explicitRequests.forEach((req: any) => {
    const rType = (req.resource_type || '').toUpperCase();
    const qStr = req.quantity ? `${req.quantity} ${req.unit || 'Units'}` : undefined;

    if (rType.includes('RESCUE') || rType.includes('BOAT')) {
      addService('RESCUE', 'Rescue & Extrication', qStr || 'Inflatable Boats & Teams', '#f59e0b', 'rgba(245, 158, 11, 0.12)', 'rgba(245, 158, 11, 0.4)', LifeBuoy, qStr, true);
    } else if (rType.includes('MEDIC') || rType.includes('HOSPITAL') || rType.includes('DOCTOR')) {
      addService('MEDICAL', 'Trauma Critical Care', qStr || 'Trauma Kits & Doctors', '#ef4444', 'rgba(239, 68, 68, 0.12)', 'rgba(239, 68, 68, 0.4)', HeartPulse, qStr, true);
    } else if (rType.includes('AMBULANCE')) {
      addService('AMBULANCE', 'ICU Mobile Ambulance', qStr || 'Emergency ICU Transit', '#ec4899', 'rgba(236, 72, 153, 0.12)', 'rgba(236, 72, 153, 0.4)', Truck, qStr, true);
    } else if (rType.includes('WATER')) {
      addService('WATER', 'Potable Water Supply', qStr || 'Drinking Water Tankers', '#06b6d4', 'rgba(6, 182, 212, 0.12)', 'rgba(6, 182, 212, 0.4)', Droplets, qStr, false);
    } else if (rType.includes('FOOD') || rType.includes('RATION')) {
      addService('FOOD', 'Emergency Food Supply', qStr || 'Dry Ready Ration Kits', '#10b981', 'rgba(16, 185, 129, 0.12)', 'rgba(16, 185, 129, 0.4)', Utensils, qStr, false);
    } else if (rType.includes('SHELTER') || rType.includes('TENT')) {
      addService('SHELTER', 'Relief Shelter Pods', qStr || 'Weatherproof Tents', '#3b82f6', 'rgba(59, 130, 246, 0.12)', 'rgba(59, 130, 246, 0.4)', Home, qStr, false);
    }
  });

  // 2. Check Needs Dictionary from AI Assessment
  if (needsDict.RESCUE || needsDict.Rescue) {
    addService('RESCUE', 'Rescue & Extrication', 'Tactical Search & Inflatable Boats', '#f59e0b', 'rgba(245, 158, 11, 0.12)', 'rgba(245, 158, 11, 0.4)', LifeBuoy, undefined, true);
  }
  if (needsDict.MEDICINE || needsDict.Medical || needsDict.MEDIC) {
    addService('MEDICAL', 'Trauma Critical Care', 'Emergency Doctors & Surgical Kits', '#ef4444', 'rgba(239, 68, 68, 0.12)', 'rgba(239, 68, 68, 0.4)', HeartPulse, undefined, true);
  }
  if (needsDict.AMBULANCE || needsDict.Ambulance) {
    addService('AMBULANCE', 'ICU Mobile Ambulance', 'Advanced Life Support Vehicles', '#ec4899', 'rgba(236, 72, 153, 0.12)', 'rgba(236, 72, 153, 0.4)', Truck, undefined, true);
  }
  if (needsDict.WATER || needsDict.Water) {
    addService('WATER', 'Potable Water Supply', 'Purified Water Units & Tankers', '#06b6d4', 'rgba(6, 182, 212, 0.12)', 'rgba(6, 182, 212, 0.4)', Droplets, undefined, false);
  }
  if (needsDict.FOOD || needsDict.Food) {
    addService('FOOD', 'Emergency Food Supply', 'High-Calorie Ready-to-Eat Rations', '#10b981', 'rgba(16, 185, 129, 0.12)', 'rgba(16, 185, 129, 0.4)', Utensils, undefined, false);
  }
  if (needsDict.SHELTER || needsDict.Shelter) {
    addService('SHELTER', 'Relief Shelter Pods', 'Family Emergency Weatherproof Tents', '#3b82f6', 'rgba(59, 130, 246, 0.12)', 'rgba(59, 130, 246, 0.4)', Home, undefined, false);
  }

  // 3. Fallback Keyword Detection from Description & Disaster Type
  if (text.includes('rescue') || text.includes('trapped') || text.includes('boat') || text.includes('flood') || text.includes('landslide') || dType.includes('flood') || dType.includes('landslide') || dType.includes('collapse')) {
    addService('RESCUE', 'Rescue & Extrication', 'Rapid Inflatable Boats & Extraction', '#f59e0b', 'rgba(245, 158, 11, 0.12)', 'rgba(245, 158, 11, 0.4)', LifeBuoy, undefined, (report.injured_people || 0) > 0 || (report.missing_people || 0) > 0);
  }

  if (text.includes('medic') || text.includes('injur') || text.includes('trauma') || text.includes('doctor') || (report.injured_people || 0) > 0) {
    addService('MEDICAL', 'Trauma Critical Care', `${report.injured_people || 'Casualty'} Triage & First-Aid Packs`, '#ef4444', 'rgba(239, 68, 68, 0.12)', 'rgba(239, 68, 68, 0.4)', HeartPulse, undefined, true);
  }

  if (text.includes('ambulance') || (report.injured_people || 0) > 3) {
    addService('AMBULANCE', 'ICU Mobile Ambulance', 'Priority Medical Transit Unit', '#ec4899', 'rgba(236, 72, 153, 0.12)', 'rgba(236, 72, 153, 0.4)', Truck, undefined, true);
  }

  if (text.includes('water') || text.includes('drink') || dType.includes('flood') || dType.includes('cyclone')) {
    addService('WATER', 'Potable Water Supply', 'Clean Drinking Water Tankers', '#06b6d4', 'rgba(6, 182, 212, 0.12)', 'rgba(6, 182, 212, 0.4)', Droplets, undefined, false);
  }

  if (text.includes('food') || text.includes('ration') || text.includes('hunger') || (report.people_affected || 0) > 20) {
    addService('FOOD', 'Emergency Food Supply', `Meal Kits for ~${report.people_affected || 10} Persons`, '#10b981', 'rgba(16, 185, 129, 0.12)', 'rgba(16, 185, 129, 0.4)', Utensils, undefined, false);
  }

  if (text.includes('shelter') || text.includes('tent') || text.includes('homeless') || dType.includes('cyclone') || dType.includes('earthquake')) {
    addService('SHELTER', 'Relief Shelter Pods', 'Temporary Evacuation Tents', '#3b82f6', 'rgba(59, 130, 246, 0.12)', 'rgba(59, 130, 246, 0.4)', Home, undefined, false);
  }

  // If still empty, supply default multi-agency package
  if (items.length === 0) {
    addService('RESCUE', 'Rapid Search & Rescue', 'First Response Squad', '#f59e0b', 'rgba(245, 158, 11, 0.12)', 'rgba(245, 158, 11, 0.4)', LifeBuoy, undefined, true);
    addService('MEDICAL', 'Emergency Medical Triage', 'Paramedic Response Team', '#ef4444', 'rgba(239, 68, 68, 0.12)', 'rgba(239, 68, 68, 0.4)', HeartPulse, undefined, false);
  }

  return items;
}

export const ServicesNeededStack: React.FC<ServicesNeededStackProps> = ({
  report,
  variant = 'compact',
}) => {
  const services = useMemo(() => extractNeededServices(report), [report]);

  if (variant === 'inline') {
    return (
      <div className="flex flex-wrap items-center gap-1.5">
        {services.map((item) => {
          const Icon = item.icon;
          return (
            <span
              key={item.id}
              style={{
                backgroundColor: item.bgColor,
                borderColor: item.borderColor,
                color: item.color,
              }}
              className="px-2 py-0.5 rounded border text-[10px] font-mono font-bold flex items-center gap-1 shadow-sm"
            >
              <Icon className="w-2.5 h-2.5" />
              <span>{item.label}</span>
              {item.quantity && <span className="opacity-80 text-[9px]">({item.quantity})</span>}
            </span>
          );
        })}
      </div>
    );
  }

  if (variant === 'compact') {
    return (
      <div className="mt-2 space-y-1.5 bg-slate-950/70 border border-slate-800/90 rounded-lg p-2.5">
        <div className="flex items-center justify-between text-[10px] font-mono font-bold text-slate-400 border-b border-slate-800/80 pb-1">
          <div className="flex items-center gap-1 text-slate-300">
            <Layers className="w-3 h-3 text-sky-400" />
            <span>SERVICES NEEDED STACK</span>
          </div>
          <span className="text-sky-400 font-bold bg-sky-950/80 border border-sky-500/30 px-1.5 py-0.2 rounded text-[9px]">
            {services.length} UNITS REQUIRED
          </span>
        </div>

        <div className="space-y-1 pt-0.5">
          {services.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.id}
                style={{
                  backgroundColor: item.bgColor,
                  borderColor: item.borderColor,
                }}
                className="px-2 py-1 rounded border flex items-center justify-between gap-2 text-[11px] font-mono transition-all"
              >
                <div className="flex items-center gap-1.5 truncate">
                  <div
                    style={{ color: item.color }}
                    className="w-4 h-4 rounded flex items-center justify-center shrink-0"
                  >
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span style={{ color: item.color }} className="font-bold text-xs truncate">
                    {item.label}
                  </span>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  <span className="text-[10px] text-slate-300 font-sans truncate max-w-[120px] sm:max-w-[150px]">
                    {item.detail}
                  </span>
                  {item.isUrgent && (
                    <span className="text-[9px] font-bold text-rose-300 bg-rose-950/90 border border-rose-500/40 px-1 py-0.2 rounded uppercase">
                      Urgent
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Full Stack Variant for Detailed Views & Reports Page
  return (
    <div className="mt-3 space-y-2 bg-slate-950/80 border border-slate-800 rounded-xl p-3 shadow-inner">
      <div className="flex items-center justify-between pb-1.5 border-b border-slate-800 text-xs font-mono">
        <div className="flex items-center gap-1.5 font-bold text-slate-200">
          <Layers className="w-3.5 h-3.5 text-sky-400" />
          <span>EMERGENCY SERVICES & RESOURCE STACK</span>
        </div>
        <span className="text-[10px] text-emerald-400 bg-emerald-950/80 border border-emerald-500/30 px-2 py-0.5 rounded font-bold">
          {services.length} ACTIVE REQUIREMENTS
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
        {services.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.id}
              style={{
                backgroundColor: item.bgColor,
                borderColor: item.borderColor,
              }}
              className="p-2.5 rounded-lg border flex flex-col justify-between space-y-1.5 relative overflow-hidden"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <div
                    style={{ color: item.color }}
                    className="w-5 h-5 rounded-md flex items-center justify-center"
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <span style={{ color: item.color }} className="font-bold text-xs font-mono">
                    {item.label}
                  </span>
                </div>

                {item.isUrgent ? (
                  <span className="text-[9px] font-mono font-black text-rose-400 bg-rose-950 border border-rose-500/50 px-1.5 py-0.2 rounded">
                    URGENT
                  </span>
                ) : (
                  <span className="text-[9px] font-mono text-slate-400 bg-slate-900 border border-slate-800 px-1.5 py-0.2 rounded">
                    REQUIRED
                  </span>
                )}
              </div>

              <div className="text-[11px] text-slate-300 font-sans pl-1 border-l-2 border-slate-700/60 leading-tight">
                {item.detail}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
