from sqlalchemy import Integer,String,Enum,ForeignKey,UUID,DateTime
import uuid
from sqlalchemy.orm import Mapped,mapped_column,relationship
import enum
from config.database import Base
import datetime

class TaskStatus(str,enum.Enum):
    TO_DO="to_do"
    DOING="doing"
    DONE="done"

class TaskPriority(str,enum.Enum):
    LOW="low"
    MEDIUM="medium"
    HIGH="high"

class Task(Base):
    __tablename__ = "task_table"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.TO_DO)

    team_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("teams_table.id", ondelete="SET NULL"),
    nullable=True
)
    
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users_table.id", ondelete="CASCADE"), nullable=False)

    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("users_table.id", ondelete="SET NULL"),
    nullable=True
)
    is_deleted: Mapped[bool] = mapped_column(default=False)

    team: Mapped["Teams | None"] = relationship(
    "Teams",
    back_populates="tasks"
)

    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], back_populates="tasks_created")
    assignee: Mapped["User | None"] = relationship(
    "User",
    foreign_keys=[assignee_id],
    back_populates="tasks_assigned"
)