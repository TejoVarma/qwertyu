import math
from typing import Any
import numpy as np
from app.core.config import settings


class MetricsCalculator:
    """
    High-performance statistical metrics calculator for UK Day-Ahead wind forecast evaluation.
    Computes industry-standard error metrics (MAE, RMSE, Bias, nMAE), energy volumes (MWh),
    P90/P95 downside shortfall risk, diurnal Settlement Period profiles, and daily roll-ups.
    """

    def __init__(self, installed_capacity_mw: float | None = None):
        self.installed_capacity_mw = installed_capacity_mw or settings.INSTALLED_WIND_CAPACITY_MW

    def calculate_daily_summary(self, points: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Calculates executive KPIs for a single Day-Ahead delivery day (48 Settlement Periods).
        """
        if not points:
            return {
                "total_expected_generation_mwh": 0.0,
                "total_actual_generation_mwh": 0.0,
                "volume_imbalance_mwh": 0.0,
                "day_mae_mw": 0.0,
                "day_rmse_mw": 0.0,
                "day_bias_mw": 0.0,
                "normalized_mae_pct": 0.0,
                "peak_shortfall_mw": 0.0,
                "p90_shortfall_mw": 0.0,
            }

        forecasts = np.array([p["forecast_mw"] for p in points], dtype=np.float64)
        actuals = np.array([p["actual_mw"] for p in points], dtype=np.float64)
        errors = np.array([p["error_mw"] for p in points], dtype=np.float64)
        shortfalls = np.array([p["shortfall_mw"] for p in points], dtype=np.float64)

        # In the UK 30-minute market: MWh = MW * 0.5 hours
        total_expected_mwh = float(np.sum(forecasts * 0.5))
        total_actual_mwh = float(np.sum(actuals * 0.5))
        volume_imbalance_mwh = total_expected_mwh - total_actual_mwh

        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        bias = float(np.mean(errors))
        nmae_pct = float((mae / self.installed_capacity_mw) * 100.0)

        peak_shortfall = float(np.max(shortfalls))
        p90_shortfall = float(np.percentile(shortfalls, 90))

        return {
            "total_expected_generation_mwh": round(total_expected_mwh, 1),
            "total_actual_generation_mwh": round(total_actual_mwh, 1),
            "volume_imbalance_mwh": round(volume_imbalance_mwh, 1),
            "day_mae_mw": round(mae, 1),
            "day_rmse_mw": round(rmse, 1),
            "day_bias_mw": round(bias, 1),
            "normalized_mae_pct": round(nmae_pct, 2),
            "peak_shortfall_mw": round(peak_shortfall, 1),
            "p90_shortfall_mw": round(p90_shortfall, 1),
        }

    def calculate_monthly_metrics(
        self, points: list[dict[str, Any]], month_label: str = "January 2026"
    ) -> dict[str, Any]:
        """
        Computes comprehensive quantitative evaluation statistics across an entire month:
        - Overall summary metrics (MAE, RMSE, Bias, nMAE, P90/P95)
        - Diurnal breakdown across all 48 Settlement Periods
        - Daily roll-up table (Jan 1 to Jan 31)
        """
        if not points:
            return {
                "evaluation_month": month_label,
                "total_periods_evaluated": 0,
                "mae_mw": 0.0,
                "rmse_mw": 0.0,
                "mean_bias_mw": 0.0,
                "normalized_mae_pct": 0.0,
                "p90_shortfall_mw": 0.0,
                "p95_shortfall_mw": 0.0,
                "diurnal_profile": [],
                "daily_summary": [],
            }

        forecasts = np.array([p["forecast_mw"] for p in points], dtype=np.float64)
        actuals = np.array([p["actual_mw"] for p in points], dtype=np.float64)
        errors = np.array([p["error_mw"] for p in points], dtype=np.float64)
        shortfalls = np.array([p["shortfall_mw"] for p in points], dtype=np.float64)

        n = len(points)
        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        bias = float(np.mean(errors))
        nmae_pct = float((mae / self.installed_capacity_mw) * 100.0)

        p90_shortfall = float(np.percentile(shortfalls, 90))
        p95_shortfall = float(np.percentile(shortfalls, 95))

        over_forecast_count = int(np.sum(errors > 0))
        under_forecast_count = int(np.sum(errors < 0))

        # 1. Diurnal profile grouped by Settlement Period (1 to 48)
        sp_groups: dict[int, list[dict[str, Any]]] = {sp: [] for sp in range(1, 49)}
        for p in points:
            sp = p["settlement_period"]
            if sp in sp_groups:
                sp_groups[sp].append(p)

        diurnal_profile = []
        for sp in range(1, 49):
            group = sp_groups[sp]
            if not group:
                continue

            g_fcsts = np.array([x["forecast_mw"] for x in group])
            g_acts = np.array([x["actual_mw"] for x in group])
            g_errs = np.array([x["error_mw"] for x in group])
            g_shorts = np.array([x["shortfall_mw"] for x in group])

            # Format half-hour label (e.g. SP 1 -> "00:00", SP 2 -> "00:30")
            h = (sp - 1) // 2
            m = 30 if (sp % 2 == 0) else 0
            time_label = f"{h:02d}:{m:02d}"

            diurnal_profile.append({
                "settlement_period": sp,
                "time_label": time_label,
                "sample_count": len(group),
                "avg_forecast_mw": round(float(np.mean(g_fcsts)), 1),
                "avg_actual_mw": round(float(np.mean(g_acts)), 1),
                "mae_mw": round(float(np.mean(np.abs(g_errs))), 1),
                "rmse_mw": round(float(np.sqrt(np.mean(g_errs ** 2))), 1),
                "bias_mw": round(float(np.mean(g_errs)), 1),
                "p90_shortfall_mw": round(float(np.percentile(g_shorts, 90)), 1),
            })

        # 2. Daily roll-up table (grouped by calendar day)
        day_groups: dict[str, list[dict[str, Any]]] = {}
        for p in points:
            d_str = p["start_time"].strftime("%Y-%m-%d")
            day_groups.setdefault(d_str, []).append(p)

        daily_summary = []
        for d_str in sorted(day_groups.keys()):
            group = day_groups[d_str]
            g_fcsts = np.array([x["forecast_mw"] for x in group])
            g_acts = np.array([x["actual_mw"] for x in group])
            g_errs = np.array([x["error_mw"] for x in group])
            g_shorts = np.array([x["shortfall_mw"] for x in group])

            daily_summary.append({
                "date": d_str,
                "periods_count": len(group),
                "expected_mwh": round(float(np.sum(g_fcsts * 0.5)), 1),
                "actual_mwh": round(float(np.sum(g_acts * 0.5)), 1),
                "mae_mw": round(float(np.mean(np.abs(g_errs))), 1),
                "rmse_mw": round(float(np.sqrt(np.mean(g_errs ** 2))), 1),
                "bias_mw": round(float(np.mean(g_errs)), 1),
                "peak_shortfall_mw": round(float(np.max(g_shorts)), 1),
            })

        return {
            "evaluation_month": month_label,
            "total_periods_evaluated": n,
            "installed_capacity_benchmark_mw": self.installed_capacity_mw,
            "mae_mw": round(mae, 1),
            "rmse_mw": round(rmse, 1),
            "mean_bias_mw": round(bias, 1),
            "normalized_mae_pct": round(nmae_pct, 2),
            "p90_shortfall_mw": round(p90_shortfall, 1),
            "p95_shortfall_mw": round(p95_shortfall, 1),
            "over_forecast_count": over_forecast_count,
            "under_forecast_count": under_forecast_count,
            "diurnal_profile": diurnal_profile,
            "daily_summary": daily_summary,
        }
