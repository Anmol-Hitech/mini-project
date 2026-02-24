from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.database import get_db
from auth.dependency import get_current_user
from schemas.teams import TeamsCreate,TeamsCreateResponse,AssignTeamRequest
from models.teams import Teams,UserTeam
from models.users import User
import uuid
from datetime import datetime, timezone
from utils.email_validator import is_valid_email_regex
from sqlalchemy.exc import IntegrityError
teamrouter=APIRouter()

@teamrouter.post("/create-team", response_model=TeamsCreateResponse)
async def create_team(
    data: TeamsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "employee":
        raise HTTPException(status_code=403, detail="Access denied")

    creator_name = current_user.name  

    new_team = Teams(
        name=data.name,
        created_by_id=current_user.id,
    )

    db.add(new_team)
    await db.flush()

    db.add(UserTeam(
        user_id=current_user.id,
        team_id=new_team.id,
        joined_at=datetime.now(timezone.utc)
    ))

    await db.commit()

    return {
        "name": new_team.name,
        "created_by": creator_name
    }
@teamrouter.post("/assign-team")
async def assign_team(
    data: AssignTeamRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "manager":
        raise HTTPException(
            status_code=403,
            detail="Only manager can assign team"
        )

    team = await db.get(Teams, data.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.created_by_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only assign users to your own teams"
        )

    user = await db.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        db.add(UserTeam(
            user_id=data.user_id,
            team_id=data.team_id,
            joined_at=datetime.now(timezone.utc)
        ))
        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="User already assigned to this team"
        )

    return {"message": "User assigned to team successfully"}