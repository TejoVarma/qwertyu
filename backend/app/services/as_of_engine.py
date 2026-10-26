from datetime import date, datetime, timedelta, timezone
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings


# For every half-hour of delivery day D, pick the latest forecast published at or
# before D-1 at :cutoff_hour (UTC), and join it with the metered actual.
# The cutoff is derived per row, so one query serves a single day or a whole month.
_AS_OF_RANGE_SQL = text("""
    SELECT DISTINCT ON (wa.start_time)
        wa.start_time,
        wa.settlement_period,
        wf.publish_time AS selected_publish_time,
        wf.generation AS forecast_mw,
        wa.generation AS actual_mw
    FROM wind_actuals wa
    JOIN wind_forecasts wf
      ON wf.start_time = wa.start_time
     AND wf.publish_time <= date_trunc('day', wa.start_time AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'
                            - INTERVAL '1 day' + make_interval(hours => :cutoff_hour)
    WHERE wa.start_time >= :range_start
      AND wa.start_time < :range_end
    ORDER BY wa.start_time, wf.publish_time DESC
""")

# For a forecast horizon of h hours, pick for each target half-hour the latest
# forecast published at least h hours before it.
_HORIZON_SQL = text("""
    SELECT DISTINCT ON (wa.start_time)
        wf.generation AS forecast_mw,
        wa.generation AS actual_mw
    FROM wind_actuals wa
    JOIN wind_forecasts wf
      ON wf.start_time = wa.start_time
     AND wf.publish_time <= wa.start_time - make_interval(hours => :horizon_hours)
    WHERE wa.start_time >= :range_start
      AND wa.start_time < :range_end
    ORDER BY wa.start_time, wf.publish_time DESC
""")


def _day_start(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _to_point(row: Any) -> dict[str, Any]:
    forecast = float(row["forecast_mw"])
    actual = float(row["actual_mw"])
    error = forecast - actual
    return {
        "settlement_period": int(row["settlement_period"]),
        "start_time": row["start_time"],
        "selected_publish_time": row["selected_publish_time"],
        "forecast_mw": round(forecast, 1),
        "actual_mw": round(actual, 1),
        "error_mw": round(error, 1),
        # Wind delivered less than forecast: the volume that must be bought elsewhere.
        "shortfall_mw": round(max(0.0, error), 1),
    }


class AsOfEngine:
    """
    Point-in-time query engine joining WINDFOR forecasts with FUELHH actuals.
    Only forecasts published at or before the decision cutoff on D-1 are considered,
    so every result reflects what a trader could actually have seen when bidding.
    """

    @staticmethod
    def calculate_cutoff_timestamp(delivery_date: date, cutoff_hour: int | None = None) -> datetime:
        """UTC decision cutoff for delivery day D: D-1 at cutoff_hour (default 11:00)."""
        hour = cutoff_hour if cutoff_hour is not None else settings.DEFAULT_DECISION_CUTOFF_HOUR
        return _day_start(delivery_date) - timedelta(days=1) + timedelta(hours=hour)

    async def get_range_snapshot(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        cutoff_hour: int | None = None,
    ) -> list[dict[str, Any]]:
        """All delivery half-hours in start_date..end_date (inclusive), each with its own D-1 cutoff."""
        hour = cutoff_hour if cutoff_hour is not None else settings.DEFAULT_DECISION_CUTOFF_HOUR
        result = await session.execute(
            _AS_OF_RANGE_SQL,
            {
                "cutoff_hour": hour,
                "range_start": _day_start(start_date),
                "range_end": _day_start(end_date) + timedelta(days=1),
            },
        )
        return [_to_point(row) for row in result.mappings().all()]

    async def get_day_ahead_snapshot(
        self,
        session: AsyncSession,
        delivery_date: date,
        cutoff_hour: int | None = None,
    ) -> dict[str, Any]:
        """The 48 settlement periods of one delivery day, as seen at the D-1 cutoff."""
        points = await self.get_range_snapshot(session, delivery_date, delivery_date, cutoff_hour)
        return {
            "delivery_date": delivery_date,
            "decision_cutoff_used": self.calculate_cutoff_timestamp(delivery_date, cutoff_hour),
            "periods_count": len(points),
            "settlement_periods": points,
        }

    async def get_horizon_pairs(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        horizon_hours: int,
    ) -> list[tuple[float, float]]:
        """(forecast, actual) pairs using the latest forecast issued at least horizon_hours before each target."""
        result = await session.execute(
            _HORIZON_SQL,
            {
                "horizon_hours": horizon_hours,
                "range_start": _day_start(start_date),
                "range_end": _day_start(end_date) + timedelta(days=1),
            },
        )
        return [(float(r["forecast_mw"]), float(r["actual_mw"])) for r in result.mappings().all()]
