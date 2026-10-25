from datetime import date, datetime, timedelta, timezone
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings


class AsOfEngine:
    """
    Core temporal query engine that executes strict As-Of Point-in-Time joins
    between Elexon wind forecasts (WINDFOR) and actual wind generation (FUELHH).
    Eliminates look-ahead bias by strictly considering forecasts published
    on or before the market decision cutoff (Day-Ahead Gate Closure).
    """

    @staticmethod
    def calculate_cutoff_timestamp(
        delivery_date: date, cutoff_hour: int | None = None
    ) -> datetime:
        """
        Calculates the UTC cutoff timestamp for Day-Ahead Gate Closure.
        Default: 11:00 UTC on D-1 (the day before delivery).
        """
        hour = cutoff_hour if cutoff_hour is not None else settings.DEFAULT_DECISION_CUTOFF_HOUR
        day_start = datetime(delivery_date.year, delivery_date.month, delivery_date.day, 0, 0, tzinfo=timezone.utc)
        return day_start - timedelta(days=1) + timedelta(hours=hour)

    async def get_day_ahead_snapshot(
        self,
        session: AsyncSession,
        delivery_date: date,
        cutoff_hour: int | None = None,
        custom_cutoff: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Retrieves the exact 48 Settlement Periods for a delivery day, matching each
        physical actual generation point against the latest forecast available
        at or before the decision cutoff.
        """
        day_start = datetime(delivery_date.year, delivery_date.month, delivery_date.day, 0, 0, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        
        cutoff_dt = custom_cutoff or self.calculate_cutoff_timestamp(delivery_date, cutoff_hour)

        query = text("""
            SELECT DISTINCT ON (wf.start_time)
                wf.start_time,
                wf.settlement_period,
                wf.publish_time AS selected_publish_time,
                ROUND(wf.generation::numeric, 1) AS forecast_mw,
                ROUND(wa.generation::numeric, 1) AS actual_mw,
                ROUND((wf.generation - wa.generation)::numeric, 1) AS error_mw,
                GREATEST(0.0, ROUND((wf.generation - wa.generation)::numeric, 1)) AS shortfall_mw
            FROM wind_forecasts wf
            INNER JOIN wind_actuals wa ON wf.start_time = wa.start_time
            WHERE wf.publish_time <= :cutoff_dt
              AND wf.start_time >= :day_start
              AND wf.start_time < :day_end
            ORDER BY wf.start_time, wf.publish_time DESC;
        """)

        result = await session.execute(
            query,
            {
                "cutoff_dt": cutoff_dt,
                "day_start": day_start,
                "day_end": day_end,
            },
        )
        rows = result.mappings().all()

        points = [
            {
                "settlement_period": int(row["settlement_period"]),
                "start_time": row["start_time"],
                "selected_publish_time": row["selected_publish_time"],
                "forecast_mw": float(row["forecast_mw"]),
                "actual_mw": float(row["actual_mw"]),
                "error_mw": float(row["error_mw"]),
                "shortfall_mw": float(row["shortfall_mw"]),
            }
            for row in rows
        ]

        return {
            "delivery_date": delivery_date,
            "decision_cutoff_used": cutoff_dt,
            "periods_count": len(points),
            "settlement_periods": points,
        }

    async def get_range_snapshot(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        cutoff_hour: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieves Day-Ahead snapshots across multiple delivery days (e.g. all of January 2026),
        where each individual delivery day D applies its own cutoff on D-1.
        Used for monthly quantitative accuracy evaluation.
        """
        all_points: list[dict[str, Any]] = []
        curr = start_date
        while curr <= end_date:
            day_result = await self.get_day_ahead_snapshot(session, curr, cutoff_hour=cutoff_hour)
            all_points.extend(day_result["settlement_periods"])
            curr += timedelta(days=1)
        return all_points
