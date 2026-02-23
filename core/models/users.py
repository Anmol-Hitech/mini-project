from sqlalchemy import Enum, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from config.database import Base
import uuid


class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class User(Base):
    __tablename__ = "users_table"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    teams: Mapped[list["Teams"]] = relationship(
        "Teams",
        foreign_keys="Teams.created_by_id",
        back_populates="creator"
    )

    user_teams: Mapped[list["UserTeam"]] = relationship(
        "UserTeam",
        foreign_keys="UserTeam.user_id",
        cascade="all, delete",
        back_populates="users"
    )

    tasks_create: Mapped[list["Task"]] = relationship(
        "Task",
        foreign_keys="Task.creator_id",
        cascade="all, delete",
        back_populates="creator"
    )

    tasks_assign: Mapped[list["Task"]] = relationship(
        "Task",
        foreign_keys="Task.assignee_id",
        cascade="all, delete",
        back_populates="assignee"
    )

    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog",
        foreign_keys="ActivityLog.user_id",
        cascade="all, delete",
        back_populates="user"
    )