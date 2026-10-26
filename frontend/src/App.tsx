import React, { useEffect } from 'react';
import { useTraderStore } from './store/useTraderStore';
import { Navbar } from './components/Navbar';
import { KpiCards } from './components/KpiCards';
import { SettlementChart } from './components/SettlementChart';
import { ProcurementTab } from './components/ProcurementTab';
import { AccuracyLab } from './components/AccuracyLab';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const {
    activeTab,
    isLoading,
    error,
    decisionData,
    loadAll,
    fetchDecision,
  } = useTraderStore();

  useEffect(() => {
    loadAll();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation & Controls */}
      <Navbar />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-6 py-6">
        
        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-200 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => fetchDecision()}
              className="px-3 py-1 rounded-lg bg-rose-900/60 hover:bg-rose-800 font-mono text-[11px] flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          </div>
        )}

        {/* Global Executive KPI Cards */}
        <KpiCards />

        {/* Active Tab View */}
        {activeTab === 'decision' && (
          <div className="space-y-6">
            <SettlementChart />
            
            {/* Quick Context Strip */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
              <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                <span className="text-slate-400 block mb-1">DECISION CUTOFF</span>
                <span className="text-white font-bold">{decisionData ? new Date(decisionData.decision_cutoff_used).toISOString().slice(0, 16).replace('T', ' ') : '--'} UTC</span>
                <p className="text-[11px] text-slate-500 mt-1">Only forecasts published at or before this time are used: exactly what the desk could see when bidding.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                <span className="text-slate-400 block mb-1">IMBALANCE RISK</span>
                <span className="text-rose-400 font-bold">Wind below forecast = short position</span>
                <p className="text-[11px] text-slate-500 mt-1">Any shortfall not covered day-ahead must be bought later, intraday or at imbalance prices.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                <span className="text-slate-400 block mb-1">RELATIVE ERROR</span>
                <span className="text-cyan-400 font-bold">{decisionData?.normalized_mae_pct ?? 0}% of mean generation</span>
                <p className="text-[11px] text-slate-500 mt-1">Day MAE divided by the day's mean metered wind output.</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'procurement' && <ProcurementTab />}

        {activeTab === 'monthly' && <AccuracyLab />}

        {activeTab === 'dailylog' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white">Daily Performance: January 2026 Decisions</h2>
                <p className="text-xs text-slate-400">Delivery days 2 Jan to 1 Feb: forecast energy at decision time vs metered energy.</p>
              </div>
            </div>
            <AccuracyLab />
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-4 px-4 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>WindProcure IQ • UK Day-Ahead Decision Support System</span>
          <span className="text-[11px]">Data Source: Elexon BMRS (FUELHH WIND & WINDFOR) • January 2026 decisions</span>
          <span className="text-cyan-500/80">React 18 • TypeScript • Zustand • FastAPI • PostgreSQL</span>
        </div>
      </footer>
    </div>
  );
};
