import React from 'react';
import { Wind, Activity, TrendingUp, Flame, AlertTriangle } from 'lucide-react';
import { useTraderStore } from '../store/useTraderStore';

export const KpiCards: React.FC = () => {
  const { decisionData, procurementData, isLoading } = useTraderStore();

  if (isLoading || !decisionData) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 rounded-xl bg-slate-900/60 border border-slate-800 animate-pulse" />
        ))}
      </div>
    );
  }

  const isOverForecast = decisionData.day_bias_mw > 0;
  const imbalanceMwh = decisionData.volume_imbalance_mwh;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      
      {/* 1. Expected Wind Generation */}
      <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-sm relative overflow-hidden group hover:border-cyan-500/40 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider font-medium text-slate-400">Day-Ahead Expected</span>
          <div className="p-2 rounded-lg bg-cyan-950/80 text-cyan-400 border border-cyan-800/50">
            <Wind className="w-4 h-4" />
          </div>
        </div>
        <div className="text-2xl font-bold font-mono text-white tracking-tight">
          {decisionData.total_expected_generation_mwh.toLocaleString()} <span className="text-sm font-normal text-slate-400">MWh</span>
        </div>
        <div className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
          <span className="text-cyan-400 font-mono font-medium">48 SPs</span>
          <span>• Locked at 11:00 UTC</span>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />
      </div>

      {/* 2. Actual Physical Generation & Imbalance */}
      <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-sm relative overflow-hidden group hover:border-emerald-500/40 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider font-medium text-slate-400">Actual Metered Flow</span>
          <div className="p-2 rounded-lg bg-emerald-950/80 text-emerald-400 border border-emerald-800/50">
            <Activity className="w-4 h-4" />
          </div>
        </div>
        <div className="text-2xl font-bold font-mono text-white tracking-tight">
          {decisionData.total_actual_generation_mwh.toLocaleString()} <span className="text-sm font-normal text-slate-400">MWh</span>
        </div>
        <div className="text-xs mt-1 flex items-center gap-1.5">
          <span className={`font-mono font-medium ${imbalanceMwh > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {imbalanceMwh > 0 ? `-${Math.abs(imbalanceMwh).toLocaleString()} MWh Deficit` : `+${Math.abs(imbalanceMwh).toLocaleString()} MWh Surplus`}
          </span>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent" />
      </div>

      {/* 3. Forecast Accuracy (MAE & Bias) */}
      <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-sm relative overflow-hidden group hover:border-purple-500/40 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider font-medium text-slate-400">Forecast Precision (MAE)</span>
          <div className="p-2 rounded-lg bg-purple-950/80 text-purple-400 border border-purple-800/50">
            <TrendingUp className="w-4 h-4" />
          </div>
        </div>
        <div className="text-2xl font-bold font-mono text-white tracking-tight">
          {decisionData.day_mae_mw.toLocaleString()} <span className="text-sm font-normal text-slate-400">MW</span>
        </div>
        <div className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
          <span className="font-mono text-purple-300">RMSE: {decisionData.day_rmse_mw} MW</span>
          <span>• nMAE: {decisionData.normalized_mae_pct}%</span>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-purple-500/50 to-transparent" />
      </div>

      {/* 4. Thermal Reserve Buffer & Risk Advisory */}
      <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-sm relative overflow-hidden group hover:border-amber-500/40 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider font-medium text-slate-400">Thermal Safety Hedge</span>
          <div className="p-2 rounded-lg bg-amber-950/80 text-amber-400 border border-amber-800/50">
            <Flame className="w-4 h-4" />
          </div>
        </div>
        <div className="text-2xl font-bold font-mono text-amber-300 tracking-tight">
          +{procurementData?.average_thermal_buffer_mw || 0} <span className="text-sm font-normal text-slate-400">MW avg</span>
        </div>
        <div className="text-xs mt-1 flex items-center gap-1.5">
          {isOverForecast ? (
            <span className="text-rose-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 inline" /> Over-forecast: Shortfall risk
            </span>
          ) : (
            <span className="text-emerald-400">
              Under-forecast: Spill risk
            </span>
          )}
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />
      </div>

    </div>
  );
};
