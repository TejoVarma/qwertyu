import uuid
from datetime import datetime
from sqlalchemy import Column, SmallInteger, Float, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class WindForecast(Base):
    """
    Represents published wind generation forecasts from National Grid ESO / Elexon,
    sourced from Elexon BMRS WINDFOR/stream.
    """
    __tablename__ = "wind_forecasts"

    # UUID Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Target delivery half-hour start timestamp (UTC)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # When this forecast was published/issued by ESO (UTC)
    publish_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Settlement Period index (1 to 48)
    settlement_period = Column(SmallInteger, nullable=False)
    
    # Forecasted electricity generation (MW)
    generation = Column(Float, nullable=False)
    
    # Metadata record creation timestamp
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # Ensure idempotent ingestion: only one forecast value per (target_time, publish_time)
        UniqueConstraint("start_time", "publish_time", name="uq_forecast_target_publish"),
        # Composite B-tree index enabling sub-10ms As-Of point-in-time range scans
        Index("idx_forecasts_as_of", "start_time", "publish_time"),
    )

    def __repr__(self) -> str:
        return f"<WindForecast(id={self.id}, SP={self.settlement_period}, target={self.start_time}, published={self.publish_time}, gen={self.generation}MW)>"
