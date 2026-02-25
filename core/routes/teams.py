from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from config.database import get_db
from auth.dependency import get_current_user
from schemas.teams import TeamsCreate,TeamsCreateResponse,AssignTeamRequest,GetTeam,TeamDetailResponse,TeamMemberStats,TeamRead,ManagerDetails
from models.teams import Teams,UserTeam
from models.users import User
from models.tasks import Task
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
    if team.is_deleted==True:
        raise HTTPException(
            status_code=400,
            detail="Team deleted"
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

@teamrouter.get("/get-team/{team_id}",response_model=GetTeam)
async def get_team(team_id:uuid.UUID,db:AsyncSession=Depends(get_db),current_user:User=Depends(get_current_user)):
    result=await db.execute(select(Teams).where(Teams.id==team_id))
    db_team=result.scalars().first()
    if not db_team:
        raise HTTPException(status_code=400,detail={"No team found"})
    if db_team.created_by_id!=current_user.id:
        raise HTTPException(status_code=400,detail={"No No access your team only"})
    return{
        "team_id":db_team.id,
        "name":db_team.name,
        "created_by_id":db_team.created_by_id,
        "is_deleted":db_team.is_deleted
    }

@teamrouter.get("/delete-team/{team_id}",response_model=GetTeam)
async def get_team(team_id:uuid.UUID,db:AsyncSession=Depends(get_db),current_user:User=Depends(get_current_user)):
    result=await db.execute(select(Teams).where(Teams.id==team_id))
    db_team=result.scalars().first()
    if not db_team:
        raise HTTPException(status_code=400,detail={"No team found"})
    if db_team.created_by_id!=current_user.id:
        raise HTTPException(status_code=400,detail={"No No access your team only"})
    if db_team.is_deleted==True:
        raise HTTPException(status_code=400,detail="Team already deleted")
    db_team.is_deleted=True
    await db.commit()
    return {"message":"Team deleted successfully"}

@teamrouter.get("/get-team-details/{team_id}", response_model=TeamDetailResponse)
async def get_team_details(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = (
        await db.execute(
            select(Teams).where(
                Teams.id == team_id,
                Teams.is_deleted == False,
            )
        )
    ).scalar_one_or_none()
 
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
 
    if current_user.role =="admin":
        pass
 
    elif current_user.role =="manager":
        if team.created_by_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        membership = (
            await db.execute(
                select(UserTeam).where(
                    UserTeam.team_id == team_id,
                    UserTeam.user_id == current_user.id,
                )
            )
        ).scalar_one_or_none()
 
        if not membership:
            raise HTTPException(status_code=403, detail="Access denied")
 
    task_count = (
        await db.execute(
            select(func.count(Task.id)).where(
                Task.team_id == team_id,
                Task.is_deleted == False,
            )
        )
    ).scalar()
 
    member_count = (
        await db.execute(
            select(func.count(UserTeam.user_id)).where(
                UserTeam.team_id == team_id,
            )
        )
    ).scalar()
 
    manager = (
        await db.execute(select(User).where(User.id == team.created_by_id))
    ).scalar_one()
 
    members = (
        (
            await db.execute(
                select(User)
                .join(UserTeam, User.id == UserTeam.user_id)
                .where(UserTeam.team_id == team_id)
            )
        )
        .scalars()
        .all()
    )
 
    members_data = []
 
    for member in members:
        user_task_count = (
            await db.execute(
                select(func.count(Task.id)).where(
                    Task.assignee_id == member.id,
                    Task.team_id == team_id,
                    Task.is_deleted == False,
                )
            )
        ).scalar()
 
        members_data.append(
            TeamMemberStats(
                id=member.id,
                name=member.name,
                email=member.email,
                task_count=user_task_count,
            )
        )
 
    return TeamDetailResponse(
        team_id=team.id,
        team_name=team.name,
        task_count=task_count,
        member_count=member_count,
        manager=ManagerDetails(
            id=manager.id,
            name=manager.name,
            email=manager.email,
        ),
        members=members_data,
    )