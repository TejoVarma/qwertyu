import pytest
from datetime import date, datetime, timezone
from app.services.elexon_service import ElexonService
from app.services.as_of_engine import AsOfEngine
from app.services.metrics_calculator import MetricsCalculator
from app.services.procurement_advisor import ProcurementAdvisor


def test_settlement_period_calculation():
    """Verifies that UTC timestamps map to correct UK Settlement Periods (1 to 48)."""
    elexon = ElexonService()
    
    # SP 1: 00:00 - 00:30 UTC
    assert elexon.calculate_settlement_period(datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)) == 1
    assert elexon.calculate_settlement_period(datetime(2026, 1, 15, 0, 29, tzinfo=timezone.utc)) == 1

    # SP 2: 00:30 - 01:00 UTC
    assert elexon.calculate_settlement_period(datetime(2026, 1, 15, 0, 30, tzinfo=timezone.utc)) == 2

    # SP 35: 17:00 - 17:30 UTC (Evening Peak)
    assert elexon.calculate_settlement_period(datetime(2026, 1, 15, 17, 0, tzinfo=timezone.utc)) == 35
    assert elexon.calculate_settlement_period(datetime(2026, 1, 15, 17, 15, tzinfo=timezone.utc)) == 35

    # SP 48: 23:30 - 00:00 UTC (Final period of day)
    assert elexon.calculate_settlement_period(datetime(2026, 1, 15, 23, 30, tzinfo=timezone.utc)) == 48


def test_as_of_cutoff_calculation():
    """Verifies that Day-Ahead Gate Closure cutoff timestamp is strictly calculated on D-1."""
    as_of = AsOfEngine()
    delivery_date = date(2026, 1, 15)
    
    # Default cutoff: 11:00 UTC on D-1
    cutoff_11 = as_of.calculate_cutoff_timestamp(delivery_date, cutoff_hour=11)
    assert cutoff_11 == datetime(2026, 1, 14, 11, 0, tzinfo=timezone.utc)

    # Custom cutoff: 14:00 UTC on D-1
    cutoff_14 = as_of.calculate_cutoff_timestamp(delivery_date, cutoff_hour=14)
    assert cutoff_14 == datetime(2026, 1, 14, 14, 0, tzinfo=timezone.utc)


def test_metrics_calculator_mathematical_precision():
    """Verifies statistical formulations: MAE, RMSE, Mean Bias, and nMAE."""
    calc = MetricsCalculator(installed_capacity_mw=30000.0)

    # Known synthetic test points
    test_points = [
        {"forecast_mw": 1100.0, "actual_mw": 1000.0, "error_mw": 100.0, "shortfall_mw": 100.0},
        {"forecast_mw": 900.0, "actual_mw": 1000.0, "error_mw": -100.0, "shortfall_mw": 0.0},
        {"forecast_mw": 1200.0, "actual_mw": 1000.0, "error_mw": 200.0, "shortfall_mw": 200.0},
        {"forecast_mw": 800.0, "actual_mw": 1000.0, "error_mw": -200.0, "shortfall_mw": 0.0},
    ]

    res = calc.calculate_daily_summary(test_points)

    # MAE = (|100| + |-100| + |200| + |-200|) / 4 = 600 / 4 = 150.0
    assert res["day_mae_mw"] == 150.0

    # Mean Bias = (100 - 100 + 200 - 200) / 4 = 0.0
    assert res["day_bias_mw"] == 0.0

    # RMSE = sqrt((100^2 + 100^2 + 200^2 + 200^2) / 4) = sqrt(100000 / 4) = sqrt(25000) = 158.1
    assert res["day_rmse_mw"] == 158.1
    assert res["day_rmse_mw"] >= res["day_mae_mw"]

    # nMAE % = (150.0 / 30000.0) * 100 = 0.5%
    assert res["normalized_mae_pct"] == 0.5

    # Peak Shortfall = max(100, 0, 200, 0) = 200.0
    assert res["peak_shortfall_mw"] == 200.0


def test_procurement_advisor_hedging_logic():
    """Verifies that higher risk tolerance produces higher safety reserve buffers."""
    advisor = ProcurementAdvisor()

    test_points = [
        {
            "settlement_period": 35,
            "forecast_mw": 10000.0,
            "actual_mw": 9000.0,
            "shortfall_mw": 1000.0,
        }
    ]

    # Consumer demand at SP 35 is ~37,620 MW (Evening peak)
    res_aggressive = advisor.calculate_procurement_schedule(test_points, risk_tolerance=0.5, peak_demand_mw=38000.0)
    res_standard = advisor.calculate_procurement_schedule(test_points, risk_tolerance=1.0, peak_demand_mw=38000.0)
    res_conservative = advisor.calculate_procurement_schedule(test_points, risk_tolerance=1.5, peak_demand_mw=38000.0)

    # Net demand should be identical
    p_agg = res_aggressive["schedule"][0]
    p_std = res_standard["schedule"][0]
    p_con = res_conservative["schedule"][0]

    assert p_agg["net_demand_mw"] == p_std["net_demand_mw"] == p_con["net_demand_mw"]

    # Safety buffer scales with risk tolerance coefficient alpha
    assert p_con["thermal_safety_buffer_mw"] > p_std["thermal_safety_buffer_mw"] > p_agg["thermal_safety_buffer_mw"]
    assert p_std["thermal_safety_buffer_mw"] == 1000.0  # 1.0 * 1000 MW shortfall
    assert p_agg["thermal_safety_buffer_mw"] == 500.0   # 0.5 * 1000 MW shortfall
    assert p_con["thermal_safety_buffer_mw"] == 1500.0  # 1.5 * 1000 MW shortfall
