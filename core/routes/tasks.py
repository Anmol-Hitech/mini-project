from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.database import get_db
from auth.dependency import get_current_user
from schemas.tasks import TaskCreate,TaskCreateRes,TaskDetailResponse,TaskStatusUpdate,TaskPriority,BulkTaskCreate,TaskStatsPriority,TaskStats,AssignTeamSchema,AssignUserSchema,TaskUniversalUpdate,UpdateTask,TaskBulkCreate,TaskBulkDelete
from models.users import User, RoleEnum
from models.teams import Teams
from models.tasks import Task,TaskStatus
from models.teams import UserTeam
import uuid
from utils.email_validator import is_valid_email_regex
from utils.email_send import send_task_completion_email

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

@taskrouter.patch("/update-task/{task_id}")
async def update_task(
    task_id: uuid.UUID,
    data: TaskUniversalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.created_by_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only task creator can update this task"
        )

    if hasattr(data, "status"):
        raise HTTPException(
            status_code=400,
            detail="Status cannot be updated from this endpoint"
        )

    if data.title is not None:
        task.title = data.title.strip()

    if data.description is not None:
        task.description = data.description

    if data.priority is not None:
        task.priority = data.priority

    if data.team_id is not None:
        team = await db.get(Teams, data.team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if team.created_by_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only assign task to your own teams"
            )

        task.team_id = data.team_id
        task.assignee_id = None  

    if data.assignee_id is not None:
        if not task.team_id:
            raise HTTPException(
                status_code=400,
                detail="Task must belong to a team before assigning user"
            )

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

    return {"message": "Task updated successfully"}
@taskrouter.delete("/delete-task/{task_id}")
async def soft_delete_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.is_deleted:
        raise HTTPException(status_code=400, detail="Task already deleted")

    if task.created_by_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only task creator can delete this task"
        )

    task.is_deleted = True

    await db.commit()

    return {"message": "Task deleted successfully"}
@taskrouter.get("/view-task/{task_id}", response_model=TaskDetailResponse)
async def view_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.is_deleted == False
        )
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    creator = await db.get(User, task.created_by_id)

    assignee_name = None
    if task.assignee_id:
        assignee = await db.get(User, task.assignee_id)
        assignee_name = assignee.name if assignee else None

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "created_by": creator.name if creator else None,
        "team_id": task.team_id,
        "assigned_to": assignee_name
    }
@taskrouter.patch("/update-status/{task_id}")
async def update_task_status(
    background_tasks:BackgroundTasks,
    task_id: uuid.UUID,
    data: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.is_deleted == False
        )
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if current_user.role=="admin":
        raise HTTPException(status_code=403,detail="Admin not allowed")
    
    if not task.assignee_id and current_user.role==RoleEnum.EMPLOYEE:
        raise HTTPException(
            status_code=400,
            detail="Task is not assigned to any employee"
        )

    if task.assignee_id != current_user.id and current_user.role==RoleEnum.EMPLOYEE:
        raise HTTPException(
            status_code=403,
            detail="You can only update your assigned tasks"
        )
    if current_user.role=="employee" and data.status=="done":
        created_id=task.created_by_id
        result2=await db.execute(select(User).where(User.id==created_id))
        db_creator=result2.scalars().first()
        creator_email=db_creator.email
        task_title=task.title
        background_tasks.add_task(send_task_completion_email,creator_email,task_title)
        print(f"DEBUG: Email task added for {current_user.email} regarding {task_title}")
    task.status = data.status

    await db.commit()
    await db.refresh(task)

    return {
        "message": "Task status updated successfully",
        "new_status": task.status
    }

#-------------BULK-API---------------#
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
 
from auth.dependency import require_roles

@taskrouter.post("/bulk-create", response_model=List[TaskCreateRes])
async def bulk_create_tasks(
    tasks: List[TaskCreate],
    user: User = Depends(require_roles("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    if not tasks:
        raise HTTPException(status_code=400, detail="Task list cannot be empty")
 
    new_tasks = [Task(**task.model_dump(), created_by_id=user.id) for task in tasks]
 
    try:
        db.add_all(new_tasks)
        await db.commit()
 
        for task in new_tasks:
            await db.refresh(task)
 
        return new_tasks
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Bulk upload failed")
 
 
@taskrouter.patch("/bulk-update", response_model=List[TaskCreate])
async def bulk_update_tasks(
    updates: List[UpdateTask],
    user: User = Depends(require_roles("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    if not updates:
        raise HTTPException(status_code=400, detail="Update list cannot be empty")
 
    task_ids = [u.task_id for u in updates]
    query = select(Task).where(Task.id.in_(task_ids))
    result = await db.execute(query)
    existing_tasks = {t.id: t for t in result.scalars().all()}
 
    if len(existing_tasks) != len(task_ids):
        raise HTTPException(status_code=404, detail="Kuch task IDs database mein nahi mile")
 
    updated_objects = []
    for update_data in updates:
        target_task = existing_tasks.get(update_data.task_id)
 
        if user.role == "manager" and target_task.created_by_id != user.id:
            raise HTTPException(
                status_code=403,
                detail=f"Task {target_task.id} aapki nahi hai, update nahi kar sakte"
            )
 
        update_dict = update_data.model_dump(exclude_unset=True, exclude={"task_id"})
        for key, value in update_dict.items():
            setattr(target_task, key, value)
 
        updated_objects.append(target_task)
 
    try:
        await db.commit()
        for t in updated_objects:
            await db.refresh(t)
        return updated_objects
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Bulk update failed")
 
 
@taskrouter.delete("/bulk-delete")
async def bulk_delete_tasks(
    data: TaskBulkDelete,
    user: User = Depends(require_roles("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    try:
        fetch_query = select(Task).where(Task.id.in_(data.task_ids))
        fetch_result = await db.execute(fetch_query)
        existing_tasks = fetch_result.scalars().all()
        existing_ids = {t.id for t in existing_tasks}
 
        if len(existing_ids) != len(data.task_ids):
            raise HTTPException(
                status_code=404, detail="Kuch task IDs database mein nahi mile"
            )
 
        if user.role == "manager":
            unauthorized_tasks = [
                t for t in existing_tasks if t.created_by_id != user.id
            ]
            if unauthorized_tasks:
                raise HTTPException(
                    status_code=403,
                    detail="Aap kisi aur manager ki task delete nahi kar sakte",
                )
 
        delete_query = delete(Task).where(Task.id.in_(data.task_ids))
        await db.execute(delete_query)
        await db.commit()
 
        return {"message": "Bulk delete successful"}
 
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Server error during bulk delete {e}")