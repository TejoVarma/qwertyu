from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from pathlib import Path
from datetime import date

# Resolve base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Central application settings managing environment configuration,
    database connection strings (local vs Neon), and domain parameters.
    """
    PROJECT_NAME: str = "UK Day-Ahead Wind Procurement Decision Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    
    # Database Connection String
    # Defaults to local PostgreSQL on 5432, seamlessly overrides with Neon URL in production
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://tejovarmaalluri@localhost:5432/wind_procure_iq",
        description="Async SQLAlchemy PostgreSQL connection string"
    )
    
    # Elexon BMRS API Configuration
    ELEXON_BASE_URL: str = "https://data.elexon.co.uk/bmrs/api/v1"
    ELEXON_API_KEY: str = ""
    
    # Day-Ahead Gate Closure Cutoff (11:00 UTC on D-1 by default in the UK wholesale market)
    DEFAULT_DECISION_CUTOFF_HOUR: int = Field(
        default=11,
        ge=0,
        le=23,
        description="Hour of day on D-1 for Day-Ahead market gate closure (0-23 UTC)"
    )
    
    # Evaluation window: delivery days whose purchase decision falls in January 2026
    # (decision on D-1, so delivery runs from 2 Jan to 1 Feb).
    EVALUATION_START_DATE: date = date(2026, 1, 2)
    EVALUATION_END_DATE: date = date(2026, 2, 1)

    # Trailing settled days used to size the procurement safety buffer
    BUFFER_LOOKBACK_DAYS: int = Field(default=14, ge=1, le=60)

    # Forecast horizons (hours before delivery) evaluated by the horizon analysis
    HORIZON_HOURS: list[int] = [1, 2, 4, 6, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48]

    # CORS Origins for Frontend Integration
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_db_url(cls, v: str) -> str:
        """
        Normalizes database URLs to ensure compatibility with SQLAlchemy's asyncpg dialect.
        Handles both local Postgres and Neon serverless strings.
        """
        if not v:
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/wind_procure_iq"
        
        v = v.strip()
        # Convert postgres:// (common in Heroku/Neon) to postgresql+asyncpg://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        # Convert standard postgresql:// to postgresql+asyncpg://
        elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Normalize Neon/libpq query parameters for asyncpg compatibility
        if "sslmode=require" in v:
            v = v.replace("sslmode=require", "ssl=require")
        if "&channel_binding=require" in v:
            v = v.replace("&channel_binding=require", "")
        if "?channel_binding=require&" in v:
            v = v.replace("?channel_binding=require&", "?")
        if "?channel_binding=require" in v:
            v = v.replace("?channel_binding=require", "")
            
        return v


settings = Settings()
