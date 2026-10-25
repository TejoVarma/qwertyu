import React from 'react';
import { Wind, Clock, ShieldAlert, Activity, Calendar } from 'lucide-react';
import { useTraderStore, TabType } from '../store/useTraderStore';

export const Navbar: React.FC = () => {
  const {
    selectedDate,
    cutoffHour,
    riskTolerance,
    activeTab,
    health,
    setSelectedDate,
    setCutoffHour,
    setRiskTolerance,
    setActiveTab,
  } = useTraderStore();

  const getRiskBadge = () => {
    if (riskTolerance < 0.8) return { label: 'Aggressive (0.5x)', color: 'bg-emerald-950/80 text-emerald-400 border-emerald-800' };
    if (riskTolerance <= 1.2) return { label: 'P90 Balanced (1.0x)', color: 'bg-cyan-950/80 text-cyan-400 border-cyan-800' };
    return { label: 'Conservative (1.5x)', color: 'bg-amber-950/80 text-amber-400 border-amber-800' };
  };

  const riskBadge = getRiskBadge();

  return (
    <header className="border-b border-slate-800/80 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-4 lg:px-6 py-3">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        
        {/* Brand & Market Identity */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Wind className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-white tracking-tight">WindProcure<span className="text-cyan-400">IQ</span></span>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800/60 text-cyan-300">
                  GB Day-Ahead
                </span>
              </div>
              <p className="text-xs text-slate-400">Elexon BMRS Decision Support & Procurement Cockpit</p>
            </div>
          </div>

          {/* Health Pill for Mobile */}
          <div className="lg:hidden flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs">
            <span className={`w-2 h-2 rounded-full ${health?.database_connected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-slate-300 font-mono text-[11px]">{health?.actuals_count ? `${health.actuals_count} SPs` : 'Offline'}</span>
          </div>
        </div>

        {/* Trader Parameter Controls */}
        <div className="flex flex-wrap items-center gap-3 bg-slate-950/60 border border-slate-800 p-2 rounded-xl">
          
          {/* 1. Date Selector (January 2026) */}
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800">
            <Calendar className="w-4 h-4 text-cyan-400" />
            <div className="flex flex-col">
              <span className="text-[10px] uppercase text-slate-400 font-medium tracking-wider">Delivery Day (D)</span>
              <input
                type="date"
                min="2026-01-01"
                max="2026-01-31"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-transparent text-xs font-mono text-white focus:outline-none cursor-pointer"
              />
            </div>
          </div>

          {/* 2. Gate Closure Cutoff Hour */}
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800">
            <Clock className="w-4 h-4 text-amber-400" />
            <div className="flex flex-col">
              <span className="text-[10px] uppercase text-slate-400 font-medium tracking-wider">Gate Closure (D-1)</span>
              <select
                value={cutoffHour}
                onChange={(e) => setCutoffHour(Number(e.target.value))}
                className="bg-transparent text-xs font-mono text-white focus:outline-none cursor-pointer"
              >
                <option value={6} className="bg-slate-900">06:00 UTC (Early Outlook)</option>
                <option value={9} className="bg-slate-900">09:00 UTC (Pre-Auction)</option>
                <option value={11} className="bg-slate-900">11:00 UTC (Official Gate)</option>
                <option value={14} className="bg-slate-900">14:00 UTC (Post-Auction)</option>
              </select>
            </div>
          </div>

          {/* 3. Risk Tolerance Slider */}
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800">
            <ShieldAlert className="w-4 h-4 text-emerald-400" />
            <div className="flex flex-col">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] uppercase text-slate-400 font-medium tracking-wider">Risk Buffer</span>
                <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${riskBadge.color}`}>
                  {riskBadge.label}
                </span>
              </div>
              <input
                type="range"
                min="0.5"
                max="1.5"
                step="0.25"
                value={riskTolerance}
                onChange={(e) => setRiskTolerance(parseFloat(e.target.value))}
                className="w-24 accent-cyan-400 h-1 bg-slate-700 rounded cursor-pointer mt-1"
              />
            </div>
          </div>

          {/* Live Data Badge for Desktop */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-900/60 text-xs text-emerald-300">
            <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
            <div className="flex flex-col">
              <span className="text-[9px] uppercase tracking-wider text-emerald-400/80 font-bold">Elexon Live Stream</span>
              <span className="font-mono text-[11px] text-emerald-200">
                {health?.forecasts_count ? `${health.forecasts_count.toLocaleString()} forecasts` : 'Connecting...'}
              </span>
            </div>
          </div>

        </div>

      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto flex items-center gap-2 mt-3 pt-2 border-t border-slate-800/60 overflow-x-auto">
        <button
          onClick={() => setActiveTab('decision')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'decision'
              ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          Day-Ahead Cockpit (48 SPs)
        </button>

        <button
          onClick={() => setActiveTab('procurement')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'procurement'
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          Thermal Procurement Advisor
        </button>

        <button
          onClick={() => setActiveTab('monthly')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'monthly'
              ? 'bg-purple-500/15 text-purple-400 border border-purple-500/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          Accuracy Lab & Diurnal Heatmap
        </button>

        <button
          onClick={() => setActiveTab('dailylog')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'dailylog'
              ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          January 2026 Daily Log
        </button>
      </div>
    </header>
  );
};
