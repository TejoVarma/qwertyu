import uuid
from datetime import datetime
from sqlalchemy import Column, SmallInteger, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class WindActual(Base):
    """
    Represents actual physical wind generation across Great Britain,
    sourced from Elexon BMRS FUELHH/stream (where fuelType == 'WIND').
    """
    __tablename__ = "wind_actuals"

    # UUID Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # 30-minute settlement period start timestamp (UTC)
    start_time = Column(DateTime(timezone=True), nullable=False, unique=True, index=True)
    
    # Settlement Period index (1 to 48 in standard UK days, up to 50 on clock change)
    settlement_period = Column(SmallInteger, nullable=False)
    
    # Actual electricity generated (MW)
    generation = Column(Float, nullable=False)
    
    # Metadata record creation timestamp
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_actuals_start_time", "start_time"),
    )

    def __repr__(self) -> str:
        return f"<WindActual(id={self.id}, SP={self.settlement_period}, start_time={self.start_time}, generation={self.generation}MW)>"
