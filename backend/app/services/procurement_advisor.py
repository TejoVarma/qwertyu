import numpy as np
from typing import Any


class ProcurementAdvisor:
    """
    Translates wind forecast predictions and quantified P90 error distributions
    into actionable Day-Ahead thermal procurement targets for utility trading desks.
    """

    @staticmethod
    def get_baseline_consumer_demand_profile(peak_demand_mw: float = 38000.0) -> list[float]:
        """
        Illustrative 48-period winter demand shape (in MW), scaled to peak_demand_mw.
        A placeholder for the client's own demand forecast, which is outside the Elexon wind dataset.
        - Overnight Base (SPs 1-12, 00:00-06:00): ~22,000 - 24,000 MW
        - Morning Peak (SPs 15-18, 07:00-09:00): ~33,000 - 35,000 MW
        - Midday Plateau (SPs 19-32, 09:30-16:00): ~30,000 - 32,000 MW
        - Evening Peak (SPs 34-38, 16:30-19:00): up to peak_demand_mw (~38,000 MW)
        - Night Taper (SPs 39-48, 19:30-23:30): down to ~24,000 MW
        """
        # Baseline normalized demand shape (fraction of peak) across 48 settlement periods
        base_shape = [
            # 00:00 - 05:30 (SPs 1-12)
            0.62, 0.60, 0.58, 0.57, 0.56, 0.55, 0.55, 0.56, 0.58, 0.62, 0.68, 0.74,
            # 06:00 - 11:30 (SPs 13-24)
            0.80, 0.86, 0.90, 0.91, 0.90, 0.88, 0.86, 0.85, 0.84, 0.83, 0.83, 0.83,
            # 12:00 - 17:30 (SPs 25-36)
            0.82, 0.82, 0.82, 0.83, 0.84, 0.86, 0.89, 0.94, 0.98, 1.00, 0.99, 0.97,
            # 18:00 - 23:30 (SPs 37-48)
            0.94, 0.91, 0.87, 0.82, 0.78, 0.74, 0.71, 0.68, 0.66, 0.64, 0.63, 0.62,
        ]
        return [round(factor * peak_demand_mw, 1) for factor in base_shape]

    @staticmethod
    def historical_p90_shortfall_by_period(history_points: list[dict[str, Any]]) -> dict[int, float]:
        """
        P90 of past shortfalls (forecast above actual) for each settlement period.
        history_points must only contain delivery days fully settled before the decision cutoff.
        """
        by_sp: dict[int, list[float]] = {}
        for p in history_points:
            by_sp.setdefault(p["settlement_period"], []).append(p["shortfall_mw"])
        return {sp: float(np.percentile(vals, 90)) for sp, vals in by_sp.items()}

    def calculate_procurement_schedule(
        self,
        settlement_points: list[dict[str, Any]],
        history_points: list[dict[str, Any]],
        risk_tolerance: float = 1.0,
        peak_demand_mw: float = 38000.0,
        custom_demand: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        Illustrative 48-period thermal requirement for the trading desk:
        Thermal Target = max(0, Demand - Wind Forecast) + risk_tolerance * historical P90 shortfall for that period.
        Demand is an input supplied by the user (it is not part of the Elexon wind data),
        and the buffer uses only errors observed before the decision, never the delivery day's actuals.
        """
        demand_profile = custom_demand or self.get_baseline_consumer_demand_profile(peak_demand_mw)
        p90_by_sp = self.historical_p90_shortfall_by_period(history_points)

        points_sorted = sorted(settlement_points, key=lambda p: p["settlement_period"])

        schedule = []
        total_demand_mwh = 0.0
        total_wind_expected_mwh = 0.0
        total_thermal_mwh = 0.0
        total_buffer_mwh = 0.0

        for i, point in enumerate(points_sorted):
            sp = point["settlement_period"]
            demand_mw = demand_profile[min(i, len(demand_profile) - 1)]
            wind_forecast_mw = point["forecast_mw"]
            actual_wind_mw = point.get("actual_mw", 0.0)

            net_demand_mw = max(0.0, demand_mw - wind_forecast_mw)
            safety_buffer_mw = round(risk_tolerance * p90_by_sp.get(sp, 0.0), 1)

            thermal_target_mw = round(net_demand_mw + safety_buffer_mw, 1)
            curtailment_spill_mw = round(max(0.0, wind_forecast_mw - demand_mw), 1)

            total_demand_mwh += demand_mw * 0.5
            total_wind_expected_mwh += wind_forecast_mw * 0.5
            total_thermal_mwh += thermal_target_mw * 0.5
            total_buffer_mwh += safety_buffer_mw * 0.5

            h = (sp - 1) // 2
            m = 30 if (sp % 2 == 0) else 0
            time_label = f"{h:02d}:{m:02d}"

            schedule.append({
                "settlement_period": sp,
                "time_label": time_label,
                "consumer_demand_mw": round(demand_mw, 1),
                "wind_forecast_mw": wind_forecast_mw,
                # Shown for back-testing only; never used in the calculation above.
                "actual_wind_mw": actual_wind_mw,
                "net_demand_mw": round(net_demand_mw, 1),
                "thermal_safety_buffer_mw": safety_buffer_mw,
                "recommended_thermal_target_mw": thermal_target_mw,
                "curtailment_spill_risk_mw": curtailment_spill_mw,
            })

        # Risk label
        if risk_tolerance < 0.75:
            risk_label = "Aggressive (Low Hedge)"
        elif risk_tolerance <= 1.25:
            risk_label = "Balanced (P90 Hedge)"
        else:
            risk_label = "Conservative (High Hedge)"

        avg_buffer_mw = (total_buffer_mwh * 2.0) / len(schedule) if schedule else 0.0

        return {
            "risk_tolerance_coefficient": risk_tolerance,
            "risk_tolerance_label": risk_label,
            "peak_consumer_demand_mw": peak_demand_mw,
            "total_consumer_demand_mwh": round(total_demand_mwh, 1),
            "total_expected_wind_mwh": round(total_wind_expected_mwh, 1),
            "total_recommended_thermal_procurement_mwh": round(total_thermal_mwh, 1),
            "total_thermal_safety_reserve_mwh": round(total_buffer_mwh, 1),
            "average_thermal_buffer_mw": round(avg_buffer_mw, 1),
            "schedule": schedule,
        }
