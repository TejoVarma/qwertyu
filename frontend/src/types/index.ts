export interface SettlementPeriodPoint {
  settlement_period: number;
  start_time: string;
  selected_publish_time: string;
  forecast_mw: number;
  actual_mw: number;
  error_mw: number;
  shortfall_mw: number;
}

export interface DayAheadDecisionResponse {
  delivery_date: string;
  decision_cutoff_used: string;
  periods_count: number;
  total_expected_generation_mwh: number;
  total_actual_generation_mwh: number;
  volume_imbalance_mwh: number;
  day_mae_mw: number;
  day_rmse_mw: number;
  day_bias_mw: number;
  normalized_mae_pct: number;
  peak_shortfall_mw: number;
  p90_shortfall_mw: number;
  settlement_periods: SettlementPeriodPoint[];
}

export interface DiurnalPeriodMetric {
  settlement_period: number;
  time_label: string;
  sample_count: number;
  avg_forecast_mw: number;
  avg_actual_mw: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  p90_shortfall_mw: number;
}

export interface DailySummaryItem {
  date: string;
  periods_count: number;
  expected_mwh: number;
  actual_mwh: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  peak_shortfall_mw: number;
}

export interface MonthlyAccuracyMetrics {
  evaluation_month: string;
  total_periods_evaluated: number;
  installed_capacity_benchmark_mw: number;
  mae_mw: number;
  rmse_mw: number;
  mean_bias_mw: number;
  normalized_mae_pct: number;
  p90_shortfall_mw: number;
  p95_shortfall_mw: number;
  over_forecast_count: number;
  under_forecast_count: number;
  diurnal_profile: DiurnalPeriodMetric[];
  daily_summary: DailySummaryItem[];
}

export interface ProcurementSchedulePoint {
  settlement_period: number;
  time_label: string;
  consumer_demand_mw: number;
  wind_forecast_mw: number;
  actual_wind_mw: number;
  net_demand_mw: number;
  thermal_safety_buffer_mw: number;
  recommended_thermal_target_mw: number;
  curtailment_spill_risk_mw: number;
}

export interface ProcurementAdvisorResponse {
  delivery_date: string;
  decision_cutoff_used: string;
  risk_tolerance_coefficient: number;
  risk_tolerance_label: string;
  peak_consumer_demand_mw: number;
  total_consumer_demand_mwh: number;
  total_expected_wind_mwh: number;
  total_recommended_thermal_procurement_mwh: number;
  total_thermal_safety_reserve_mwh: number;
  average_thermal_buffer_mw: number;
  schedule: ProcurementSchedulePoint[];
}

export interface HealthStatus {
  status: string;
  database_connected: boolean;
  actuals_count: number;
  forecasts_count: number;
  version: string;
  timestamp: string;
}
