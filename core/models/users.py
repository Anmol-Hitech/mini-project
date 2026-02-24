from sqlalchemy import Enum, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
import enum
from config.database import Base

class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

class User(Base):
    __tablename__ = "users_table"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    teams_created: Mapped[list["Teams"]] = relationship("Teams", back_populates="creator", cascade="all, delete")
    tasks_created: Mapped[list["Task"]] = relationship("Task", back_populates="creator", cascade="all, delete", foreign_keys="Task.created_by_id")
    tasks_assigned: Mapped[list["Task"]] = relationship("Task", back_populates="assignee", cascade="all, delete", foreign_keys="Task.assignee_id")
    user_teams: Mapped[list["UserTeam"]] = relationship("UserTeam", back_populates="user", cascade="all, delete")
    activity_logs: Mapped[list["ActivityLog"]] = relationship("ActivityLog", back_populates="user", cascade="all, delete")