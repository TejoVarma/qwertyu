import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { BarChart3, TrendingUp, AlertTriangle, ShieldCheck, Calendar } from 'lucide-react';
import { useTraderStore } from '../store/useTraderStore';

export const AccuracyLab: React.FC = () => {
  const { monthlyData } = useTraderStore();

  if (!monthlyData || monthlyData.diurnal_profile.length === 0) {
    return (
      <div className="h-96 rounded-2xl bg-slate-900/50 border border-slate-800 flex items-center justify-center text-slate-500">
        Loading January 2026 monthly accuracy data...
      </div>
    );
  }

  const diurnalChartData = monthlyData.diurnal_profile.map((d) => ({
    sp: d.settlement_period,
    time: d.time_label,
    mae: d.mae_mw,
    rmse: d.rmse_mw,
    bias: d.bias_mw,
    p90: d.p90_shortfall_mw,
  }));

  const DiurnalTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;
    const d = payload[0].payload;

    return (
      <div className="p-3 rounded-xl bg-slate-900/95 border border-slate-700 shadow-2xl backdrop-blur text-xs font-mono space-y-1.5 min-w-[220px]">
        <div className="font-bold text-white border-b border-slate-800 pb-1 flex justify-between">
          <span>SP {d.sp} ({d.time} UTC)</span>
          <span className="text-[10px] text-purple-400 font-semibold">Diurnal Average</span>
        </div>
        <div className="flex justify-between text-purple-400">
          <span className="text-slate-400">MAE (Precision):</span>
          <span className="font-bold">{d.mae.toLocaleString()} MW</span>
        </div>
        <div className="flex justify-between text-cyan-400">
          <span className="text-slate-400">RMSE (Ramp Penalizer):</span>
          <span className="font-bold">{d.rmse.toLocaleString()} MW</span>
        </div>
        <div className="flex justify-between text-slate-300">
          <span className="text-slate-400">Mean Bias:</span>
          <span className={`font-bold ${d.bias > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {d.bias > 0 ? `+${d.bias.toLocaleString()}` : d.bias.toLocaleString()} MW
          </span>
        </div>
        <div className="flex justify-between text-amber-400 border-t border-slate-800 pt-1">
          <span>P90 Shortfall Buffer:</span>
          <span className="font-bold">+{d.p90.toLocaleString()} MW</span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      
      {/* Month-Wide Executive Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
        
        {/* MAE */}
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Monthly MAE</span>
            <TrendingUp className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {monthlyData.mae_mw.toLocaleString()} <span className="text-xs text-slate-400 font-normal">MW</span>
          </div>
          <span className="text-[10px] text-purple-400 font-mono mt-0.5 inline-block">Average volumetric miss</span>
        </div>

        {/* RMSE */}
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Monthly RMSE</span>
            <BarChart3 className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {monthlyData.rmse_mw.toLocaleString()} <span className="text-xs text-slate-400 font-normal">MW</span>
          </div>
          <span className="text-[10px] text-cyan-400 font-mono mt-0.5 inline-block">Heavy penalty on ramp busts</span>
        </div>

        {/* Normalized MAE (nMAE) */}
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Normalized nMAE</span>
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-bold font-mono text-emerald-400">
            {monthlyData.normalized_mae_pct}%
          </div>
          <span className="text-[10px] text-slate-400 font-mono mt-0.5 inline-block">vs 30,000 MW GB capacity</span>
        </div>

        {/* Mean Bias Error */}
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Mean Directional Bias</span>
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-bold font-mono text-amber-300">
            {monthlyData.mean_bias_mw > 0 ? `+${monthlyData.mean_bias_mw.toLocaleString()}` : monthlyData.mean_bias_mw.toLocaleString()} <span className="text-xs text-slate-400 font-normal">MW</span>
          </div>
          <span className="text-[10px] text-rose-400 font-mono mt-0.5 inline-block">Over-forecast tendency</span>
        </div>

        {/* P90 Downside Risk */}
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>P90 Downside Risk</span>
            <ShieldCheck className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-xl font-bold font-mono text-rose-400">
            {monthlyData.p90_shortfall_mw.toLocaleString()} <span className="text-xs text-slate-400 font-normal">MW</span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono mt-0.5 inline-block">P95: {monthlyData.p95_shortfall_mw.toLocaleString()} MW</span>
        </div>

      </div>

      {/* Diurnal Error Heatmap / Bar Chart (SPs 1 to 48) */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-bold text-base text-white">Diurnal Error Profile Across 48 Settlement Periods</h3>
            <p className="text-xs text-slate-400">
              Shows how forecast error (MAE and Bias) varies across the day in January 2026. Notice higher uncertainty during evening peak (SPs 34-38).
            </p>
          </div>
          <span className="text-xs font-mono text-purple-400 bg-purple-950/60 border border-purple-800/50 px-2.5 py-1 rounded-full">
            {monthlyData.total_periods_evaluated.toLocaleString()} Half-Hours Evaluated
          </span>
        </div>

        <div className="h-[360px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={diurnalChartData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              
              <XAxis
                dataKey="time"
                stroke="#64748b"
                fontSize={10}
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
                tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
                domain={[0, 'auto']}
              />

              <Tooltip content={<DiurnalTooltip />} />
              <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ paddingBottom: 15, fontSize: 12, fontFamily: 'monospace' }} />

              <Bar dataKey="mae" name="Mean Absolute Error (MAE, MW)" fill="#a855f7" radius={[3, 3, 0, 0]} />
              <Bar dataKey="p90" name="P90 Shortfall Buffer (MW)" fill="#f59e0b" radius={[3, 3, 0, 0]} opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Daily Summary Table */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 shadow-xl">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-cyan-400" />
            <h3 className="font-bold text-sm text-white">January 2026 Daily Performance Log (31 Days)</h3>
          </div>
          <span className="text-xs font-mono text-slate-400">Locked at D-1 11:00 UTC</span>
        </div>

        <div className="max-h-72 overflow-y-auto border border-slate-800 rounded-xl">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 sticky top-0 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Date</th>
                <th className="py-2.5 px-3 font-semibold">SPs</th>
                <th className="py-2.5 px-3 font-semibold text-cyan-400">Expected (MWh)</th>
                <th className="py-2.5 px-3 font-semibold text-emerald-400">Actual (MWh)</th>
                <th className="py-2.5 px-3 font-semibold text-purple-400">MAE (MW)</th>
                <th className="py-2.5 px-3 font-semibold text-cyan-300">RMSE (MW)</th>
                <th className="py-2.5 px-3 font-semibold text-amber-400">Mean Bias</th>
                <th className="py-2.5 px-3 font-semibold text-rose-400">Peak Shortfall</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {monthlyData.daily_summary.map((day) => (
                <tr key={day.date} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2 px-3 text-white font-bold">{day.date}</td>
                  <td className="py-2 px-3 text-slate-400">{day.periods_count}</td>
                  <td className="py-2 px-3 text-cyan-300">{day.expected_mwh.toLocaleString()}</td>
                  <td className="py-2 px-3 text-emerald-300">{day.actual_mwh.toLocaleString()}</td>
                  <td className="py-2 px-3 text-purple-300">{day.mae_mw.toLocaleString()}</td>
                  <td className="py-2 px-3 text-cyan-200">{day.rmse_mw.toLocaleString()}</td>
                  <td className={`py-2 px-3 font-semibold ${day.bias_mw > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {day.bias_mw > 0 ? `+${day.bias_mw.toLocaleString()}` : day.bias_mw.toLocaleString()}
                  </td>
                  <td className="py-2 px-3 text-rose-400">{day.peak_shortfall_mw.toLocaleString()} MW</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
