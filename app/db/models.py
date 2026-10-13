import uuid
from datetime import datetime, timezone
from sqlalchemy import  String, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base

class RequestLog(Base):
    __tablename__="request_logs"
    id: Mapped[UUID]=mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    timestamp: Mapped[datetime]= mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))
    user_id: Mapped[str]=mapped_column(String, index=True, default="anonymous")
    model_used: Mapped[str]=mapped_column(String, index=True)
    prompt_tokens: Mapped[int]=mapped_column(Integer, default=0)
    completion_tokens: Mapped[int]=mapped_column(Integer, default=0)
    total_tokens: Mapped[int]=mapped_column(Integer, default=0)
    cost_usd: Mapped[float]=mapped_column(Float, default=0.0)
    latency_ms: Mapped[float]=mapped_column(Float, default=0.0)
    is_cache_hit: Mapped[bool]=mapped_column(Boolean, default=False)