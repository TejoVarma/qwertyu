import React, { useState } from 'react';
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
import { Layers, Info, CheckCircle2 } from 'lucide-react';
import { useTraderStore } from '../store/useTraderStore';

export const SettlementChart: React.FC = () => {
  const { decisionData, cutoffHour } = useTraderStore();
  const [showErrorArea, setShowErrorArea] = useState<boolean>(true);

  if (!decisionData || decisionData.settlement_periods.length === 0) {
    return (
      <div className="h-96 rounded-2xl bg-slate-900/50 border border-slate-800 flex items-center justify-center text-slate-500">
        No settlement period data available.
      </div>
    );
  }

  // Format data for Recharts
  const chartData = decisionData.settlement_periods.map((p) => {
    const sp = p.settlement_period;
    const h = Math.floor((sp - 1) / 2);
    const m = sp % 2 === 0 ? '30' : '00';
    const timeLabel = `${String(h).padStart(2, '0')}:${m}`;

    return {
      sp,
      timeLabel,
      forecast_mw: p.forecast_mw,
      actual_mw: p.actual_mw,
      error_mw: p.error_mw,
      shortfall_mw: p.shortfall_mw,
      publish_time: p.selected_publish_time,
    };
  });

  // Custom Tooltip component
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;
    const data = payload[0].payload;

    const pubDate = new Date(data.publish_time);
    const formattedPub = pubDate.toISOString().replace('T', ' ').substring(0, 16) + ' UTC';

    return (
      <div className="p-3.5 rounded-xl bg-slate-900/95 border border-slate-700/80 shadow-2xl backdrop-blur text-xs font-mono space-y-2 min-w-[240px]">
        <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
          <span className="font-bold text-white">SP {data.sp} ({data.timeLabel} UTC)</span>
          <span className="text-[10px] text-cyan-400 font-semibold bg-cyan-950/80 px-1.5 py-0.5 rounded border border-cyan-800/50">
            D-1 Locked
          </span>
        </div>

        <div className="space-y-1">
          <div className="flex justify-between items-center text-cyan-400">
            <span className="text-slate-400">Day-Ahead Forecast:</span>
            <span className="font-bold">{data.forecast_mw.toLocaleString()} MW</span>
          </div>

          <div className="flex justify-between items-center text-emerald-400">
            <span className="text-slate-400">Physical Actual Flow:</span>
            <span className="font-bold">{data.actual_mw.toLocaleString()} MW</span>
          </div>

          <div className="flex justify-between items-center text-slate-300 pt-1 border-t border-slate-800/60">
            <span className="text-slate-400">Error Delta (F - A):</span>
            <span className={`font-bold ${data.error_mw > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {data.error_mw > 0 ? `+${data.error_mw.toLocaleString()}` : data.error_mw.toLocaleString()} MW
            </span>
          </div>
        </div>

        <div className="pt-1.5 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400">
          <span>Forecast published:</span>
          <span className="text-slate-300">{formattedPub}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 shadow-xl mb-6">
      
      {/* Chart Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white tracking-tight">
              Day-Ahead Wind Generation vs. Physical Metered Actuals
            </h2>
            <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 rounded-full">
              48 Settlement Periods
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 inline" />
            <span>Point-in-time view: latest forecast published by <strong>{String(cutoffHour).padStart(2, '0')}:00 UTC on D-1</strong>.</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowErrorArea(!showErrorArea)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 border transition-all ${
              showErrorArea
                ? 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60'
                : 'bg-slate-800/60 text-slate-400 border-slate-700'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{showErrorArea ? 'Shortfall Band Visible' : 'Shortfall Band Hidden'}</span>
          </button>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-[420px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
            <defs>
              <linearGradient id="shortfallGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />

            <XAxis
              dataKey="timeLabel"
              stroke="#64748b"
              fontSize={11}
              fontFamily="monospace"
              tickLine={false}
              interval={3} // Show every 2 hours
              dy={8}
            />

            <YAxis
              stroke="#64748b"
              fontSize={11}
              fontFamily="monospace"
              tickLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
              domain={[0, 'auto']}
              label={{
                value: 'Power (MW)',
                angle: -90,
                position: 'insideLeft',
                fill: '#64748b',
                fontSize: 11,
                fontFamily: 'monospace',
                offset: 15,
              }}
            />

            <Tooltip content={<CustomTooltip />} />

            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              wrapperStyle={{ paddingBottom: 15, fontSize: 12, fontFamily: 'monospace' }}
            />

            {/* Error / Shortfall Area */}
            {showErrorArea && (
              <Area
                type="monotone"
                dataKey="shortfall_mw"
                name="Downside Shortfall Delta"
                fill="url(#shortfallGradient)"
                stroke="#ef4444"
                strokeWidth={1}
                strokeDasharray="3 3"
              />
            )}

            {/* Line 1: Day-Ahead Wind Forecast */}
            <Line
              type="monotone"
              dataKey="forecast_mw"
              name="Day-Ahead Wind Forecast (MW)"
              stroke="#38bdf8"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#38bdf8', stroke: '#070c18', strokeWidth: 2 }}
            />

            {/* Line 2: Actual Physical Generation */}
            <Line
              type="monotone"
              dataKey="actual_mw"
              name="Actual Physical Metered Flow (MW)"
              stroke="#10b981"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#10b981', stroke: '#070c18', strokeWidth: 2 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Legend & Context Explainer */}
      <div className="mt-3 pt-3 border-t border-slate-800/60 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-cyan-400 rounded-full" />
            <span>Forecast as of D-1 {String(cutoffHour).padStart(2, '0')}:00 UTC</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-emerald-400 rounded-full" />
            <span>Physical actual generation</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 bg-rose-500/20 border border-rose-500/60 rounded" />
            <span>Wind shortfall exposure</span>
          </div>
        </div>

        <div className="flex items-center gap-1 text-[11px] text-slate-400">
          <Info className="w-3.5 h-3.5 text-cyan-400 inline" />
          <span>Settlement Period resolution: 30 minutes (SPs 1 to 48)</span>
        </div>
      </div>

    </div>
  );
};
