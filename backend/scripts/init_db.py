import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import inspect
from app.core.config import settings
from app.core.database import engine, Base
from app.models import WindActual, WindForecast


async def init_tables() -> None:
    """Creates all registered database tables and indices in PostgreSQL."""
    print("=" * 60)
    print("UK DAY-AHEAD WIND POWER DECISION PLATFORM - DB INITIALIZATION")
    print("=" * 60)
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1]}")
    
    async with engine.begin() as conn:
        print("\nCreating tables: wind_actuals, wind_forecasts...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables and indices created successfully!")

        # Verify created tables
        def check_tables(connection):
            inspector = inspect(connection)
            tables = inspector.get_table_names()
            return tables

        tables = await conn.run_sync(check_tables)
        print(f"\nTables present in database: {tables}")
        
    await engine.dispose()
    print("\nInitialization complete! You can now view these tables in Beekeeper Studio.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(init_tables())
