from sqlalchemy import Integer, String, Enum, ForeignKey, UUID, DateTime
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from config.database import Base
import datetime


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users_table.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="activity_logs")
