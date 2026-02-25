from sqlalchemy import Integer, String, Enum, ForeignKey, UUID, DateTime
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from config.database import Base
import datetime


class InviteToken(Base):
    __tablename__ = "invite_table"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    token:Mapped[str]=mapped_column(
        unique=True
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams_table.id", ondelete="CASCADE"),
        nullable=False
    )

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users_table.id", ondelete="CASCADE"),
        nullable=False
    )

    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    is_used: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    team: Mapped["Teams"] = relationship(
        "Teams",
        foreign_keys=[team_id]
    )

    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id]
    )

