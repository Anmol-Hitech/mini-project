from sqlalchemy import String, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from config.database import Base
from sqlalchemy import ForeignKey, DateTime, UUID,func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import uuid
from config.database import Base
class Teams(Base):
    __tablename__ = "teams_table"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users_table.id", ondelete="CASCADE"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], back_populates="teams_created")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="team", cascade="all, delete")
    user_teams: Mapped[list["UserTeam"]] = relationship("UserTeam", back_populates="team", cascade="all, delete")


class UserTeam(Base):
    __tablename__ = "user_teams"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users_table.id", ondelete="CASCADE"), primary_key=True)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams_table.id", ondelete="CASCADE"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),   
    server_default=func.now(), 
    nullable=False
)

    user: Mapped["User"] = relationship("User", back_populates="user_teams")
    team: Mapped["Teams"] = relationship("Teams", back_populates="user_teams")