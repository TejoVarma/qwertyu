"""
Small, hand-checkable dataset for the API tests.

Delivery day D = 2026-01-15, every half-hour metered at 10,000 MW. Forecasts for D:
  - published D-2 22:30 -> 12,000 MW (older)
  - published D-1 09:30 -> 11,000 MW (latest before the 11:00 cutoff: the one a trader would use)
  - published D-1 11:30 -> 99,999 MW (after the cutoff: must never be used for the D-1 11:00 decision)

History for the procurement buffer:
  - D-2 (2026-01-13): metered 10,000, forecast (pub 2026-01-12 09:30) 10,500 -> shortfall 500 MW
  - D-1 (2026-01-14): metered 10,000, forecast (pub 2026-01-13 09:30) 15,000 -> shortfall 5,000 MW
    D-1 is not fully metered at the D-1 11:00 decision, so it must be excluded.
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

DELIVERY_DAY = datetime(2026, 1, 15, tzinfo=timezone.utc)


def _half_hours(day: datetime) -> list[datetime]:
    return [day + timedelta(minutes=30 * i) for i in range(48)]


async def seed_test_data(engine) -> None:
    actuals = []
    forecasts = []

    def add_day(day: datetime, publications: list[tuple[datetime, float]]) -> None:
        for i, t in enumerate(_half_hours(day)):
            actuals.append({"start_time": t, "sp": i + 1, "gen": 10000.0})
            for published, value in publications:
                forecasts.append({"start_time": t, "publish_time": published, "sp": i + 1, "gen": value})

    d = DELIVERY_DAY
    add_day(d - timedelta(days=2), [(d - timedelta(days=3) + timedelta(hours=9, minutes=30), 10500.0)])
    add_day(d - timedelta(days=1), [(d - timedelta(days=2) + timedelta(hours=9, minutes=30), 15000.0)])
    add_day(d, [
        (d - timedelta(days=2) + timedelta(hours=22, minutes=30), 12000.0),
        (d - timedelta(days=1) + timedelta(hours=9, minutes=30), 11000.0),
        (d - timedelta(days=1) + timedelta(hours=11, minutes=30), 99999.0),
    ])

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE wind_actuals, wind_forecasts"))
        await conn.execute(
            text("""INSERT INTO wind_actuals (id, start_time, settlement_period, generation, created_at)
                    VALUES (gen_random_uuid(), :start_time, :sp, :gen, now())"""),
            actuals,
        )
        await conn.execute(
            text("""INSERT INTO wind_forecasts (id, start_time, publish_time, settlement_period, generation, created_at)
                    VALUES (gen_random_uuid(), :start_time, :publish_time, :sp, :gen, now())"""),
            forecasts,
        )
