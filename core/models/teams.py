from sqlalchemy import Integer,String,Enum,ForeignKey,UUID,DateTime
import uuid
from sqlalchemy.orm import Mapped,mapped_column,relationship
import enum
from config.database import Base
from datetime import datetime, timezone

class Teams(Base):
    __tablename__="teams_table"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4, 
        index=True
    )
    name: Mapped[str]=mapped_column(
        nullable=False,
    )
    created_by_id:Mapped[uuid.UUID]=mapped_column(
        ForeignKey("users_table.id",ondelete="CASCADE"),nullable=False
    )
    is_deleted:Mapped[bool]=mapped_column(default=False)
    creator:Mapped["User"]=relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="teams"
    )
    user_teams:Mapped["UserTeam"]=relationship(
        "UserTeam",
        cascade="all, delete",
        back_populates="teams"
    )
    tasks:Mapped["Task"]=relationship(
        "Task",
        cascade="all, delete",
        back_populates="teams"
    )
    

class UserTeam(Base):
    __tablename__="user_teams"
    user_id:Mapped[uuid.UUID]=mapped_column(
        ForeignKey("users_table.id",ondelete="CASCADE"),nullable=False,primary_key=True
    )
    team_id:Mapped[uuid.UUID]=mapped_column(
        ForeignKey("teams_table.id",ondelete="CASCADE"),nullable=False,primary_key=True
    )
    joined_at:Mapped[datetime]=mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    users:Mapped["User"]=relationship(
            "User",
            foreign_keys=[user_id],
            back_populates="user_teams",
            cascade="all, delete"
            )
    
    teams:Mapped["Teams"]=relationship(
            "Teams",
            foreign_keys=[team_id],
            cascade="all, delete",
            back_populates="user_teams"
        )
    
