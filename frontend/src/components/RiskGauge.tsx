'use client';

import React from 'react';

interface RiskGaugeProps {
  score: number;
  level?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskGauge = ({ score, level, size = 'md' }: RiskGaugeProps) => {
  const normalizedScore = Math.max(0, Math.min(100, score || 0));

  let color = 'text-emerald-400';
  let bgColor = 'bg-emerald-500/10 border-emerald-500/30';
  let badgeColor = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';

  if (normalizedScore >= 80) {
    color = 'text-rose-500';
    bgColor = 'bg-rose-500/10 border-rose-500/30';
    badgeColor = 'bg-rose-500/20 text-rose-400 border-rose-500/40';
  } else if (normalizedScore >= 60) {
    color = 'text-orange-500';
    bgColor = 'bg-orange-500/10 border-orange-500/30';
    badgeColor = 'bg-orange-500/20 text-orange-400 border-orange-500/40';
  } else if (normalizedScore >= 35) {
    color = 'text-amber-500';
    bgColor = 'bg-amber-500/10 border-amber-500/30';
    badgeColor = 'bg-amber-500/20 text-amber-400 border-amber-500/40';
  }

  const determinedLevel = level || (
    normalizedScore >= 80 ? 'CRITICAL' :
    normalizedScore >= 60 ? 'HIGH' :
    normalizedScore >= 35 ? 'MEDIUM' : 'LOW'
  );

  return (
    <div className="flex items-center gap-3">
      <div className={`relative flex items-center justify-center rounded-xl border p-2.5 ${bgColor}`}>
        <span className={`font-black tracking-tight ${size === 'lg' ? 'text-3xl' : size === 'sm' ? 'text-sm' : 'text-xl'} ${color}`}>
          {normalizedScore.toFixed(1)}
        </span>
        <span className="text-[10px] text-slate-400 font-medium ml-0.5">/100</span>
      </div>
      <div>
        <span className={`inline-block rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${badgeColor}`}>
          {determinedLevel} RISK
        </span>
        <p className="text-[11px] text-slate-400 mt-0.5">Contextual Graph Score</p>
      </div>
    </div>
  );
};
