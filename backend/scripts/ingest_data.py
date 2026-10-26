import argparse
import asyncio
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.core.config import settings
from app.core.database import async_session_factory, engine, init_db
from app.models import WindActual, WindForecast
from app.services.elexon_service import ElexonService, ElexonFetchError


async def batch_insert(model, records: list[dict], conflict: dict, batch_size: int = 2000) -> None:
    """Inserts records idempotently using ON CONFLICT DO NOTHING."""
    async with async_session_factory() as session:
        for i in range(0, len(records), batch_size):
            stmt = pg_insert(model).values(records[i:i + batch_size]).on_conflict_do_nothing(**conflict)
            await session.execute(stmt)
        await session.commit()


async def run_ingestion(start: date, end: date, forecast_lookback_days: int, reset: bool) -> None:
    started = time.time()

    # Actuals for every delivery day in the window.
    # Forecasts published from a few days before the first delivery day (so day-ahead and
    # 48h-horizon forecasts exist for it) until the end of the last delivery day.
    publish_from = datetime(start.year, start.month, start.day, tzinfo=timezone.utc) - timedelta(days=forecast_lookback_days)
    publish_to = datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=1)

    print("=" * 70)
    print("UK DAY-AHEAD WIND - ELEXON DATA INGESTION")
    print("=" * 70)
    print(f"Actuals (FUELHH WIND), settlement dates : {start} to {end}")
    print(f"Forecasts (WINDFOR), published          : {publish_from:%Y-%m-%d %H:%M} to {publish_to:%Y-%m-%d %H:%M} UTC")
    print(f"Database                                : {settings.DATABASE_URL.split('@')[-1]}")
    print("-" * 70)

    elexon = ElexonService()
    try:
        actuals = await elexon.fetch_actual_wind(start, end)
        forecasts = await elexon.fetch_forecast_wind(publish_from, publish_to)
    except ElexonFetchError as exc:
        sys.exit(f"ERROR: Elexon fetch failed, nothing was written to the database. {exc}")

    expected_half_hours = ((end - start).days + 1) * 48
    if len(actuals) != expected_half_hours:
        print(f"WARNING: expected {expected_half_hours} actual half-hours, Elexon returned {len(actuals)}.")
    if not actuals or not forecasts:
        sys.exit("ERROR: Elexon returned no data, nothing was written to the database.")

    await init_db()
    if reset:
        async with engine.begin() as conn:
            await conn.execute(text("TRUNCATE wind_actuals, wind_forecasts"))
        print("Existing rows removed (--reset).")

    await batch_insert(WindActual, actuals, {"index_elements": ["start_time"]})
    await batch_insert(WindForecast, forecasts, {"constraint": "uq_forecast_target_publish"})

    async with async_session_factory() as session:
        actuals_count = (await session.execute(select(func.count(WindActual.id)))).scalar_one()
        forecasts_count = (await session.execute(select(func.count(WindForecast.id)))).scalar_one()
        publishes = (await session.execute(select(func.count(func.distinct(WindForecast.publish_time))))).scalar_one()

    print(f"Actuals fetched / rows in wind_actuals     : {len(actuals):,} / {actuals_count:,}")
    print(f"Forecasts fetched / rows in wind_forecasts : {len(forecasts):,} / {forecasts_count:,} ({publishes} publications)")
    print(f"Done in {time.time() - started:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Load Elexon wind actuals and forecasts into PostgreSQL.")
    # Starts in mid-December so the procurement buffer for early-January decisions has
    # BUFFER_LOOKBACK_DAYS of settled history behind it.
    parser.add_argument("--start-date", type=date.fromisoformat, default=date(2025, 12, 18),
                        help="First delivery day (default: 2025-12-18)")
    parser.add_argument("--end-date", type=date.fromisoformat, default=settings.EVALUATION_END_DATE,
                        help="Last delivery day (default: 2026-02-01)")
    parser.add_argument("--forecast-lookback-days", type=int, default=3,
                        help="Days of forecasts to load before the first delivery day (default: 3)")
    parser.add_argument("--reset", action="store_true", help="Empty both tables before loading")
    args = parser.parse_args()
    asyncio.run(run_ingestion(args.start_date, args.end_date, args.forecast_lookback_days, args.reset))


if __name__ == "__main__":
    main()
