from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, Field


# --- Health Schema ---
class HealthResponse(BaseModel):
    status: str = "ok"
    database_connected: bool
    actuals_count: int
    forecasts_count: int
    version: str
    timestamp: datetime


# --- Day-Ahead Decision Schemas ---
class SettlementPeriodPoint(BaseModel):
    settlement_period: int = Field(ge=1, le=50, description="Settlement Period index (1 to 48)")
    start_time: datetime = Field(description="Target 30-minute interval start time (UTC)")
    selected_publish_time: datetime = Field(description="Issue timestamp of the selected forecast (UTC)")
    forecast_mw: float = Field(description="Predicted wind generation in MW")
    actual_mw: float = Field(description="Physical metered wind generation in MW")
    error_mw: float = Field(description="Forecast error in MW (Forecast - Actual)")
    shortfall_mw: float = Field(description="Under-generation deficit in MW (max(0, Forecast - Actual))")


class DayAheadDecisionResponse(BaseModel):
    delivery_date: date
    decision_cutoff_used: datetime
    periods_count: int
    total_expected_generation_mwh: float
    total_actual_generation_mwh: float
    volume_imbalance_mwh: float
    day_mae_mw: float
    day_rmse_mw: float
    day_bias_mw: float
    normalized_mae_pct: float
    peak_shortfall_mw: float
    p90_shortfall_mw: float
    settlement_periods: list[SettlementPeriodPoint]


# --- Monthly Accuracy Evaluation Schemas ---
class DiurnalPeriodMetric(BaseModel):
    settlement_period: int
    time_label: str
    sample_count: int
    avg_forecast_mw: float
    avg_actual_mw: float
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    p90_shortfall_mw: float


class DailySummaryItem(BaseModel):
    date: str
    periods_count: int
    expected_mwh: float
    actual_mwh: float
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    peak_shortfall_mw: float


class MonthlyAccuracyMetrics(BaseModel):
    evaluation_month: str
    total_periods_evaluated: int
    mae_mw: float
    rmse_mw: float
    mean_bias_mw: float
    normalized_mae_pct: float = Field(description="MAE as % of mean metered wind generation")
    p90_shortfall_mw: float
    p95_shortfall_mw: float
    over_forecast_count: int
    under_forecast_count: int
    diurnal_profile: list[DiurnalPeriodMetric]
    daily_summary: list[DailySummaryItem]


# --- Procurement Advisor Schemas ---
class ProcurementSchedulePoint(BaseModel):
    settlement_period: int
    time_label: str
    consumer_demand_mw: float
    wind_forecast_mw: float
    actual_wind_mw: float
    net_demand_mw: float
    thermal_safety_buffer_mw: float
    recommended_thermal_target_mw: float
    curtailment_spill_risk_mw: float


class ProcurementAdvisorRequest(BaseModel):
    delivery_date: date = Field(default=date(2026, 1, 15), description="Target delivery day (2026-01-02 to 2026-02-01)")
    cutoff_hour: int = Field(default=11, ge=0, le=23, description="Day-Ahead Gate Closure hour on D-1 (0-23 UTC)")
    risk_tolerance: float = Field(default=1.0, ge=0.1, le=2.5, description="Risk tolerance multiplier for P90 buffer")
    peak_demand_mw: float = Field(default=38000.0, gt=0.0, description="Peak of the illustrative demand curve in MW (user input, not Elexon data)")
    custom_demand: list[float] | None = Field(default=None, min_length=48, max_length=48, description="Optional 48-point demand forecast supplied by the client")

    model_config = {
        "json_schema_extra": {
            "example": {
                "delivery_date": "2026-01-15",
                "cutoff_hour": 11,
                "risk_tolerance": 1.0,
                "peak_demand_mw": 38000.0,
            }
        }
    }


class ProcurementAdvisorResponse(BaseModel):
    delivery_date: date
    decision_cutoff_used: datetime
    buffer_history_start: date = Field(description="First settled delivery day used to size the safety buffer")
    buffer_history_end: date = Field(description="Last settled delivery day used to size the safety buffer (D-2)")
    risk_tolerance_coefficient: float
    risk_tolerance_label: str
    peak_consumer_demand_mw: float
    total_consumer_demand_mwh: float
    total_expected_wind_mwh: float
    total_recommended_thermal_procurement_mwh: float
    total_thermal_safety_reserve_mwh: float
    average_thermal_buffer_mw: float
    schedule: list[ProcurementSchedulePoint]


# --- Forecast Horizon Analysis Schemas ---
class HorizonMetric(BaseModel):
    horizon_hours: int = Field(description="Forecast issued at least this many hours before delivery")
    sample_count: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    relative_mae_pct: float = Field(description="MAE as % of mean metered wind generation")
    p90_abs_error_mw: float


class HorizonAnalysisResponse(BaseModel):
    start_date: date
    end_date: date
    horizons: list[HorizonMetric]
