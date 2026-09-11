export function getSeverityColor(severity: number | string): {
  bg: string;
  text: string;
  border: string;
  dot: string;
  glow: string;
} {
  const num = typeof severity === 'number' ? severity : parseFloat(severity);
  
  if (num >= 9.0 || severity === 'Critical') {
    return {
      bg: 'bg-red-950/60',
      text: 'text-red-400',
      border: 'border-red-500/50',
      dot: 'bg-red-500',
      glow: 'shadow-[0_0_12px_rgba(239,68,68,0.5)]',
    };
  }
  if (num >= 7.0 || severity === 'High') {
    return {
      bg: 'bg-orange-950/60',
      text: 'text-orange-400',
      border: 'border-orange-500/50',
      dot: 'bg-orange-500',
      glow: 'shadow-[0_0_12px_rgba(249,115,22,0.5)]',
    };
  }
  if (num >= 4.0 || severity === 'Moderate') {
    return {
      bg: 'bg-yellow-950/60',
      text: 'text-yellow-400',
      border: 'border-yellow-500/50',
      dot: 'bg-yellow-500',
      glow: 'shadow-[0_0_12px_rgba(234,179,8,0.5)]',
    };
  }
  return {
    bg: 'bg-emerald-950/60',
    text: 'text-emerald-400',
    border: 'border-emerald-500/50',
    dot: 'bg-emerald-500',
    glow: 'shadow-[0_0_12px_rgba(16,185,129,0.5)]',
  };
}

export function formatTimestamp(isoStr: string): string {
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  } catch {
    return isoStr;
  }
}

export function formatDateTime(isoStr: string): string {
  try {
    const d = new Date(isoStr);
    return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
  } catch {
    return isoStr;
  }
}

export function getStatusBadgeClasses(status: string): string {
  switch (status.toUpperCase()) {
    case 'AVAILABLE':
    case 'SUCCESS':
    case 'FULFILLED':
    case 'VERIFIED':
      return 'bg-emerald-950/70 text-emerald-300 border-emerald-500/30';
    case 'ALLOCATED':
    case 'IN_PROGRESS':
    case 'EN_ROUTE':
      return 'bg-sky-950/70 text-sky-300 border-sky-500/30';
    case 'DELAYED':
    case 'WARNING':
    case 'PENDING REVIEW':
      return 'bg-amber-950/70 text-amber-300 border-amber-500/30';
    case 'CRITICAL':
    case 'FAILURE':
    case 'REJECTED':
      return 'bg-rose-950/70 text-rose-300 border-rose-500/30';
    default:
      return 'bg-slate-800 text-slate-300 border-slate-700';
  }
}
