from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.database import get_db
from auth.dependency import get_current_user
from schemas.tasks import TaskCreate,TaskCreateRes,TaskPriority,BulkTaskCreate,TaskStatsPriority,TaskStats,AssignTeamSchema,AssignUserSchema
from models.users import User, RoleEnum
from models.teams import Teams
from models.tasks import Task,TaskStatus
from models.teams import UserTeam
import uuid
from utils.email_validator import is_valid_email_regex

taskrouter=APIRouter()

@taskrouter.post("/create-task", response_model=TaskCreateRes)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == RoleEnum.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Access denied")

    new_task = Task(
        title=data.title.strip(),
        description=data.description,
        priority=data.priority or TaskPriority.MEDIUM,
        status=data.status or TaskStatus.TO_DO,
        created_by_id=current_user.id,
        team_id=None,
        assignee_id=None
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return {
        "title": new_task.title,
        "description": new_task.description,
        "priority": new_task.priority,
        "status": new_task.status,
        "created_by": current_user.name,
        "assigned_to": None,
        "teams_id": None
    }
@taskrouter.patch("/assign-team/{task_id}")
async def assign_task_to_team(
    task_id: uuid.UUID,
    data: AssignTeamSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.MANAGER:
        raise HTTPException(status_code=403, detail="Only manager can assign team")

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    team = await db.get(Teams, data.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.created_by_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only assign tasks to your own teams"
        )

    task.team_id = data.team_id

    await db.commit()
    await db.refresh(task)

    return {"message": "Task assigned to team successfully"}
@taskrouter.patch("/assign-user/{task_id}")
async def assign_task_to_user(
    task_id: uuid.UUID,
    data: AssignUserSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.MANAGER:
        raise HTTPException(status_code=403, detail="Only manager can assign user")

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.team_id:
        raise HTTPException(
            status_code=400,
            detail="Task must be assigned to a team first"
        )

    team = await db.get(Teams, task.team_id)

    if team.created_by_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only assign users to tasks in your own teams"
        )

    user = await db.get(User, data.assignee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    member_check = await db.execute(
        select(UserTeam).where(
            UserTeam.user_id == data.assignee_id,
            UserTeam.team_id == task.team_id
        )
    )

    if not member_check.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="User is not a member of this team"
        )

    task.assignee_id = data.assignee_id

    await db.commit()
    await db.refresh(task)

    return {"message": "Task assigned to user successfully"}