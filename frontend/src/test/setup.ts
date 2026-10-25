import '@testing-library/jest-dom';
import { vi } from 'vitest';

vi.mock('../services/api', () => ({
  apiService: {
    getHealth: vi.fn().mockResolvedValue({
      status: 'ok',
      version: '1.0.0',
      database_connected: true,
      actuals_count: 1537,
      forecasts_count: 37376,
    }),
    getDayAheadDecision: vi.fn().mockResolvedValue({
      delivery_date: '2026-01-15',
      decision_cutoff_used: '2026-01-14T11:00:00Z',
      periods_count: 48,
      day_mae_mw: 1110.2,
      day_rmse_mw: 1228.5,
      day_bias_mw: 555.1,
      normalized_mae_pct: 3.7,
      total_expected_generation_mwh: 280272.0,
      total_actual_generation_mwh: 253626.0,
      volume_imbalance_mwh: 26646.0,
      peak_shortfall_mw: 1226.0,
      p90_shortfall_mw: 1000.0,
      settlement_periods: [],
    }),
    getMonthlyEvaluation: vi.fn().mockResolvedValue({}),
    getDailyLog: vi.fn().mockResolvedValue([]),
    calculateProcurementAdvice: vi.fn().mockResolvedValue({
      delivery_date: '2026-01-15',
      decision_cutoff_used: '2026-01-14T11:00:00Z',
      peak_consumer_demand_mw: 38000.0,
      risk_tolerance_coefficient: 1.0,
      risk_tolerance_label: 'P90 Standard Risk',
      total_consumer_demand_mwh: 760000.0,
      total_expected_wind_mwh: 280000.0,
      total_recommended_thermal_procurement_mwh: 500000.0,
      total_thermal_safety_reserve_mwh: 20000.0,
      average_thermal_buffer_mw: 833.0,
      schedule: [
        {
          settlement_period: 35,
          time_label: '17:00',
          consumer_demand_mw: 37620.0,
          wind_forecast_mw: 8966.0,
          actual_wind_mw: 8266.0,
          net_demand_mw: 28654.0,
          thermal_safety_buffer_mw: 700.0,
          recommended_thermal_target_mw: 29354.0,
          curtailment_spill_risk_mw: 0.0,
        },
      ],
    }),
  },
}));
