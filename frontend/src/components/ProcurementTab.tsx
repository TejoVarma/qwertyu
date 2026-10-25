import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { Flame, ShieldCheck, Zap, Sliders, ArrowUpRight } from 'lucide-react';
import { useTraderStore } from '../store/useTraderStore';

export const ProcurementTab: React.FC = () => {
  const {
    procurementData,
    peakDemandMw,
    riskTolerance,
    setPeakDemandMw,
    setRiskTolerance,
  } = useTraderStore();

  if (!procurementData || procurementData.schedule.length === 0) {
    return (
      <div className="h-96 rounded-2xl bg-slate-900/50 border border-slate-800 flex items-center justify-center text-slate-500">
        Loading procurement advisor data...
      </div>
    );
  }

  const chartData = procurementData.schedule.map((p) => ({
    sp: p.settlement_period,
    timeLabel: p.time_label,
    consumer_demand: p.consumer_demand_mw,
    wind_forecast: p.wind_forecast_mw,
    net_demand: p.net_demand_mw,
    thermal_target: p.recommended_thermal_target_mw,
    safety_buffer: p.thermal_safety_buffer_mw,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;
    const d = payload[0].payload;

    return (
      <div className="p-3.5 rounded-xl bg-slate-900/95 border border-slate-700 shadow-2xl backdrop-blur text-xs font-mono space-y-2 min-w-[260px]">
        <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
          <span className="font-bold text-white">SP {d.sp} ({d.timeLabel} UTC)</span>
          <span className="text-[10px] text-amber-400 font-semibold bg-amber-950/80 px-1.5 py-0.5 rounded border border-amber-800/50">
            Thermal Target
          </span>
        </div>

        <div className="space-y-1">
          <div className="flex justify-between items-center text-purple-300">
            <span className="text-slate-400">Gross Consumer Demand:</span>
            <span className="font-bold">{d.consumer_demand.toLocaleString()} MW</span>
          </div>

          <div className="flex justify-between items-center text-cyan-400">
            <span className="text-slate-400">Wind Forecast Expected:</span>
            <span className="font-bold">-{d.wind_forecast.toLocaleString()} MW</span>
          </div>

          <div className="flex justify-between items-center text-slate-300 pt-1 border-t border-slate-800">
            <span className="text-slate-400">Net Residual Demand:</span>
            <span className="font-bold">{d.net_demand.toLocaleString()} MW</span>
          </div>

          <div className="flex justify-between items-center text-emerald-400">
            <span className="text-slate-400">P90 Safety Buffer (+α):</span>
            <span className="font-bold">+{d.safety_buffer.toLocaleString()} MW</span>
          </div>

          <div className="flex justify-between items-center text-amber-400 font-bold pt-1 border-t border-slate-700">
            <span>RECOMMENDED TARGET:</span>
            <span className="text-sm">{d.thermal_target.toLocaleString()} MW</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      
      {/* Advisor Interactive Parameters & Executive Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Left: Commercial Decision Parameters */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Sliders className="w-4 h-4 text-amber-400" />
            <h3 className="font-bold text-sm text-white">Procurement Hedging Parameters</h3>
          </div>

          {/* Peak Demand Input */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Peak Consumer Demand (MW)</span>
              <span className="font-mono text-cyan-400 font-bold">{peakDemandMw.toLocaleString()} MW</span>
            </div>
            <input
              type="range"
              min="25000"
              max="50000"
              step="1000"
              value={peakDemandMw}
              onChange={(e) => setPeakDemandMw(Number(e.target.value))}
              className="w-full accent-cyan-400 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>25,000 MW (Low)</span>
              <span>38,000 MW (Winter Std)</span>
              <span>50,000 MW (Severe)</span>
            </div>
          </div>

          {/* Risk Tolerance Slider */}
          <div className="space-y-1.5 pt-2 border-t border-slate-800/60">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Risk Tolerance Multiplier (α)</span>
              <span className="font-mono text-amber-400 font-bold">{riskTolerance.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="1.5"
              step="0.1"
              value={riskTolerance}
              onChange={(e) => setRiskTolerance(parseFloat(e.target.value))}
              className="w-full accent-amber-400 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0.5x (Aggressive)</span>
              <span>1.0x (P90 Balanced)</span>
              <span>1.5x (Conservative)</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 leading-relaxed">
            <ShieldCheck className="w-4 h-4 text-emerald-400 inline mr-1.5" />
            <span>
              <strong>P90 Guarantee</strong>: Hedging with α = {riskTolerance} covers wind drop-off risks 90% of the time, protecting against cash-out imbalance spikes (£500+/MWh).
            </span>
          </div>
        </div>

        {/* Right: Executive Energy Quantities */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-4">
          
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
            <span className="text-xs uppercase text-slate-400 font-medium">Total Gross Demand</span>
            <div className="text-2xl font-bold font-mono text-white mt-2">
              {procurementData.total_consumer_demand_mwh.toLocaleString()} <span className="text-xs text-slate-400 font-normal">MWh</span>
            </div>
            <span className="text-[11px] text-purple-400 font-mono mt-1">Winter Consumer Load</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
            <span className="text-xs uppercase text-slate-400 font-medium">Wind Generation Credit</span>
            <div className="text-2xl font-bold font-mono text-cyan-400 mt-2">
              -{procurementData.total_expected_wind_mwh.toLocaleString()} <span className="text-xs text-slate-400 font-normal">MWh</span>
            </div>
            <span className="text-[11px] text-cyan-300/80 font-mono mt-1">Zero-marginal cost wind</span>
          </div>

          <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/60 flex flex-col justify-between shadow-lg shadow-amber-950/20">
            <span className="text-xs uppercase text-amber-300 font-medium">Recommended Thermal Target</span>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-2">
              {procurementData.total_recommended_thermal_procurement_mwh.toLocaleString()} <span className="text-xs text-amber-300/70 font-normal">MWh</span>
            </div>
            <span className="text-[11px] text-amber-300/90 font-mono mt-1">
              Includes +{procurementData.total_thermal_safety_reserve_mwh.toLocaleString()} MWh buffer
            </span>
          </div>

          {/* Full-width callout */}
          <div className="sm:col-span-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <Flame className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Recommended CCGT / Thermal Hedging Strategy</h4>
                <p className="text-xs text-slate-400">
                  Submit firm purchase bids for <strong className="text-amber-300">{procurementData.total_recommended_thermal_procurement_mwh.toLocaleString()} MWh</strong> in the Day-Ahead auction before 11:00 UTC.
                </p>
              </div>
            </div>
            <span className="hidden sm:inline-flex items-center gap-1 text-xs font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800 px-3 py-1.5 rounded-lg">
              <span>Ready for Auction</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </span>
          </div>

        </div>

      </div>

      {/* Main Procurement Curve Chart */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-bold text-base text-white">48 Settlement Period Procurement Schedule</h3>
            <p className="text-xs text-slate-400">
              Shows how the recommended thermal target wraps consumer demand around wind fluctuations.
            </p>
          </div>
          <span className="text-xs font-mono text-amber-400 bg-amber-950/60 border border-amber-800/50 px-2.5 py-1 rounded-full">
            {procurementData.risk_tolerance_label}
          </span>
        </div>

        <div className="h-[380px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              
              <XAxis
                dataKey="timeLabel"
                stroke="#64748b"
                fontSize={11}
                fontFamily="monospace"
                tickLine={false}
                interval={3}
                dy={8}
              />

              <YAxis
                stroke="#64748b"
                fontSize={11}
                fontFamily="monospace"
                tickLine={false}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                domain={[0, 'auto']}
              />

              <Tooltip content={<CustomTooltip />} />
              <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ paddingBottom: 15, fontSize: 12, fontFamily: 'monospace' }} />

              {/* Net Demand Area */}
              <Area
                type="monotone"
                dataKey="net_demand"
                name="Residual Net Demand (MW)"
                fill="#334155"
                fillOpacity={0.2}
                stroke="#64748b"
                strokeDasharray="2 2"
              />

              {/* Consumer Demand Curve */}
              <Line
                type="monotone"
                dataKey="consumer_demand"
                name="Gross Consumer Demand (MW)"
                stroke="#a855f7"
                strokeWidth={2}
                dot={false}
              />

              {/* Wind Forecast Curve */}
              <Line
                type="monotone"
                dataKey="wind_forecast"
                name="Day-Ahead Wind Generation (MW)"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={false}
              />

              {/* Recommended Thermal Target (with Buffer) */}
              <Line
                type="monotone"
                dataKey="thermal_target"
                name="Recommended Thermal Target (MW)"
                stroke="#f59e0b"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5, fill: '#f59e0b', stroke: '#070c18', strokeWidth: 2 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 48-Period Dispatch Table */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 shadow-xl overflow-hidden">
        <h3 className="font-bold text-sm text-white mb-3">Half-Hourly Procurement Dispatch Table</h3>
        <div className="max-h-72 overflow-y-auto border border-slate-800 rounded-xl">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 sticky top-0 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3 font-semibold">SP</th>
                <th className="py-2.5 px-3 font-semibold">Time (UTC)</th>
                <th className="py-2.5 px-3 font-semibold text-purple-400">Demand (MW)</th>
                <th className="py-2.5 px-3 font-semibold text-cyan-400">Wind (MW)</th>
                <th className="py-2.5 px-3 font-semibold text-slate-300">Net Demand</th>
                <th className="py-2.5 px-3 font-semibold text-emerald-400">Safety Buffer</th>
                <th className="py-2.5 px-3 font-semibold text-amber-400">Thermal Target</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {procurementData.schedule.map((row) => (
                <tr key={row.settlement_period} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2 px-3 text-slate-400 font-bold">{row.settlement_period}</td>
                  <td className="py-2 px-3">{row.time_label}</td>
                  <td className="py-2 px-3 text-purple-300 font-medium">{row.consumer_demand_mw.toLocaleString()}</td>
                  <td className="py-2 px-3 text-cyan-300 font-medium">{row.wind_forecast_mw.toLocaleString()}</td>
                  <td className="py-2 px-3 text-slate-400">{row.net_demand_mw.toLocaleString()}</td>
                  <td className="py-2 px-3 text-emerald-400">+{row.thermal_safety_buffer_mw.toLocaleString()}</td>
                  <td className="py-2 px-3 text-amber-300 font-bold">{row.recommended_thermal_target_mw.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
