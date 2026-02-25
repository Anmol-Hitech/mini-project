from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from config.database import get_db
from auth.auth import hash_password,verify_password,create_access_token
from auth.dependency import get_current_user
from schemas.users import CreateUser,PromoteEmp, CreateUserResponse,LoginUser,UpdateUser,UserListResponse,TeamRead
from models.users import User, RoleEnum
from models.teams import Teams,UserTeam
from models.tasks import Task,TaskStatus
import datetime
import uuid
from utils.email_validator import is_valid_email_regex

userrouter = APIRouter()


@userrouter.post("/create-user", response_model=CreateUserResponse)
async def create_user(
    data: CreateUser,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == RoleEnum.EMPLOYEE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )
    if current_user.role == RoleEnum.MANAGER.value and data.role.lower() == RoleEnum.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail="Manager cannot create admin",
        )
    if current_user.role==RoleEnum.MANAGER.value and data.role.lower()==RoleEnum.MANAGER.value:
        raise HTTPException(
            status_code=403,
            detail="Manager cannot create Manager"
        )
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    new_user = User(
        id=uuid.uuid4(),
        name=data.name.strip(),
        email=data.email.lower(),
        password=hash_password(data.password),
        role=data.role.lower(),
        is_active=True,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return CreateUserResponse(
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        is_active=new_user.is_active,
    )

@userrouter.post("/create-super-admin")
async def super_admin(db:AsyncSession=Depends(get_db)):
    admin_data = CreateUser(
        name="Anmol",
        email="anmol@gmail.com",
        password="Admin@1234",
        role="admin"
    )
    admin_data.validate_fields()
    new_admin = User(
        id=uuid.uuid4(),
        name=admin_data.name.strip(),
        email=admin_data.email.lower(),
        password=hash_password(admin_data.password),
        role=RoleEnum.ADMIN,
        is_active=True
    )
    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)
    return "Super admin created successfully!!!!"

@userrouter.post("/login")
async def login(data:LoginUser , db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(data.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    if db_user.name != data.name:
        raise HTTPException(status_code=400, detail="Incorrect username")

    if db_user.role != data.role:
        raise HTTPException(status_code=401, detail="Access denied")
    
    if db_user.is_active==False:
        raise HTTPException(status_code=400,detail="User deactivated")

    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

@userrouter.post("/deactivate/{email}")
async def deactivate(email:str,db:AsyncSession=Depends(get_db),current_user:User=Depends(get_current_user)):
    if is_valid_email_regex(email)==False:
        raise HTTPException(status_code=400,detail="Enter valid email to deactivate")
    result=await db.execute(select(User).where(User.email==email))
    db_user=result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=400,detail="No user found")
    
    if current_user.role=="manager":
        if db_user.role=="admin":
            raise HTTPException(status_code=400,detail="You cannot deactivate an admin account")
    
    if current_user.role=="employee":
        if db_user.role=="admin" or db_user.role=="manager":
            raise HTTPException(status_code=400,detail="Bro...")
    if db_user.is_active==False:
        raise HTTPException(status_code=400,detail="Acccount already deactive")
    db_user.is_active=False
    await db.commit()
    await db.refresh(db_user)
    return {"message":"User deactivated successfully"}

@userrouter.post("/activate/{email}")
async def deactivate(email:str,db:AsyncSession=Depends(get_db),current_user:User=Depends(get_current_user)):
    if is_valid_email_regex(email)==False:
        raise HTTPException(status_code=400,detail="Enter valid email to activate")
    result=await db.execute(select(User).where(User.email==email))
    db_user=result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=400,detail="No user found")
    
    if current_user.role=="manager":
        if db_user.role=="admin":
            raise HTTPException(status_code=400,detail="You cannot activate an admin account")
    
    if current_user.role=="employee":
        if db_user.role=="admin" or db_user.role=="manager":
            raise HTTPException(status_code=400,detail="Bro...")
    
    if db_user.is_active==True:
        raise HTTPException(status_code=400,detail="Account already active")
    db_user.is_active=True
    await db.commit()
    await db.refresh(db_user)
    return {"message":"User activated successfully"}

@userrouter.patch("/update/{email}",response_model=CreateUserResponse)
async def update_user(email:str,data:UpdateUser,db:AsyncSession=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role=="employee":
        raise HTTPException(status_code=400,detail="Access denied")
    result=await db.execute(select(User).where(User.email==email))
    db_user=result.scalars().first()
    if current_user.role=="manager" and db_user.role=="admin":
        raise HTTPException(status_code=400,detail="Manager cannot update admin")
    if data.email is not None:
        db_user.email=data.email
    if data.name is not None:
        db_user.name=data.name
    await db.commit()
    await db.refresh(db_user)
    return {
        "name":db_user.name,
        "email":db_user.email,
        "is_active":db_user.is_active,
        "role":db_user.role
    }

@userrouter.delete("/delete/{email}")
async def delete_user(email:str,db:AsyncSession=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role=="employee":
        raise HTTPException(status_code=400,detail="Access denied")
    result=await db.execute(select(User).where(User.email==email))
    db_user=result.scalars().first()
    if current_user.role=="manager" and db_user.role=="admin":
        raise HTTPException(status_code=400,detail="Manager cannot delete admin")
    db.delete(db_user)
    await db.commit()
    return {"message":"User deleted successfully"}


from datetime import datetime, timezone

@userrouter.patch("/promote/{email}")
async def promote_user(
    data: PromoteEmp,
    email: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_valid_email_regex(email):
        raise HTTPException(status_code=400, detail="Enter valid email")

    result = await db.execute(select(User).where(User.email == email))
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    if db_user.role == RoleEnum.ADMIN:
        raise HTTPException(status_code=400, detail="Admin cannot be promoted")

    if db_user.role == RoleEnum.EMPLOYEE:

        db_user.role = RoleEnum.MANAGER

        new_team = Teams(
            name=data.team_name,
            created_by_id=db_user.id,  
        )

        db.add(new_team)
        await db.flush()  

        db.add(UserTeam(
            user_id=db_user.id,
            team_id=new_team.id,
            joined_at=datetime.now(timezone.utc)
        ))
    await db.commit()
    await db.refresh(db_user)

    return {
        "message": "User promoted successfully",
        "new_role": db_user.role
    }

@userrouter.get("/get-profile")
async def get_profile(db:AsyncSession=Depends(get_db),current_user:User=Depends(get_current_user)):
    user_id=current_user.id
    result=await db.execute(select(UserTeam).where(UserTeam.user_id==user_id))
    result2=await db.execute(select(Task).where(Task.assignee_id==user_id))
    db_task=result2.scalars().first()
    if not db_task:
        task_id=None
        task_title=None
        task_des=None
        task_pr=None
        task_status=None
    db_user_team=result.scalars().first()
    if not db_user_team:
        assigned_team_id=None
        joined_at=None
    if db_user_team:
        assigned_team_id=db_user_team.team_id
        joined_at=db_user_team.joined_at
    result3=await db.execute(select(Teams).where(Teams.id==assigned_team_id))
    db_team=result3.scalars().first()
    team_name=None
    if db_team:
        team_name=db_team.name
    
    if db_task:
        task_id=db_task.id
        task_title=db_task.title
        task_des=db_task.description
        task_pr=db_task.priority
        task_status=db_task.status
    return{
        "user_id":current_user.id,
        "user_name":current_user.name,
        "user_email":current_user.email,
        "user_role":current_user.role,
        "team_id":assigned_team_id,
        "team_name":team_name,
        "team_joined_at":joined_at,
        "task_id":task_id,
        "task_title":task_title,
        "task_des":task_des,
        "task_pr":task_pr,
        "tas_status":task_status
    }

@userrouter.get("/get-specific-user/{user_email}")
async def get_spec(user_email:str,db:AsyncSession=Depends(get_db),current_user:User=Depends(get_current_user)):
    result=await db.execute(select(User).where(User.email==user_email))
    db_user=result.scalars().first()
    user_id=db_user.id
    result=await db.execute(select(UserTeam).where(UserTeam.user_id==user_id))
    result2=await db.execute(select(Task).where(Task.assignee_id==user_id))
    db_task=result2.scalars().first()
    db_user_team=result.scalars().first()
    assigned_team_id=None
    joined_at=None
    if db_user_team:
        assigned_team_id=db_user_team.team_id
        joined_at=db_user_team.joined_at
    result3=await db.execute(select(Teams).where(Teams.id==assigned_team_id))
    db_team=result3.scalars().first()
    team_name=None
    task_id=None
    task_title=None
    task_des=None
    task_pr=None
    task_status=None
    if db_team and db_task:
        team_name=db_team.name
        task_id=db_task.id
        task_title=db_task.title
        task_des=db_task.description
        task_pr=db_task.priority
        task_status=db_task.status
    return{
        "user_id":current_user.id,
        "user_name":current_user.name,
        "user_email":current_user.email,
        "user_role":current_user.role,
        "team_id":assigned_team_id,
        "team_name":team_name,
        "team_joined_at":joined_at,
        "task_id":task_id,
        "task_title":task_title,
        "task_des":task_des,
        "task_pr":task_pr,
        "tas_status":task_status
    }

@userrouter.get("/admin/get-all-users", response_model=list[UserListResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can access this")

    result = await db.execute(select(User))
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active
        }
        for user in users
    ]
@userrouter.get("/my-tasks")
async def get_my_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Task).where(
            Task.assignee_id == current_user.id,
            Task.is_deleted == False
        )
    )

    tasks = result.scalars().all()

    return [
        {
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "team_id": task.team_id
        }
        for task in tasks
    ]
@userrouter.get("/my-teams")
async def get_my_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(UserTeam).where(UserTeam.user_id == current_user.id)
    )

    user_teams = result.scalars().all()

    teams_data = []

    for ut in user_teams:
        team_result = await db.execute(
            select(Teams).where(Teams.id == ut.team_id)
        )
        team = team_result.scalars().first()

        if team:
            teams_data.append({
                "team_id": team.id,
                "team_name": team.name,
                "joined_at": ut.joined_at
            })

    return teams_data

@userrouter.get("/get-all-teams",response_model=list[TeamRead])
async def all_teams(db:AsyncSession=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role=="admin":
        result_teams=(
            (await db.execute(select(Teams).where(Teams.is_deleted==False))).scalars().all()
        )
        return result_teams
    if current_user.role == "manager":
        teams = (
            (
                await db.execute(
                    select(Teams).where(
                        Teams.created_by_id == current_user.id,
                        Teams.is_deleted == False,
                    )
                )
            )
            .scalars()
            .all()
        )
        return teams
 
    teams = (
        (
            await db.execute(
                select(Teams)
                .join(UserTeam, Teams.id == UserTeam.team_id)
                .where(
                    UserTeam.user_id == current_user.id,
                    Teams.is_deleted == False,
                )
            )
        )
        .scalars()
        .all()
    )
 
    return teams

@userrouter.get("/tasks/stats")
async def get_task_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base_query = select(Task.status, func.count(Task.id)).where(
        Task.is_deleted == False
    )
 
    if current_user.role == RoleEnum.ADMIN:
        query = base_query.group_by(Task.status)
 
    elif current_user.role == RoleEnum.MANAGER:
        subquery = select(Teams.id).where(
            Teams.created_by_id == current_user.id,
            Teams.is_deleted == False,
        )
 
        query = (
            base_query
            .where(Task.team_id.in_(subquery))
            .group_by(Task.status)
        )
 
    else:
        subquery = select(UserTeam.team_id).where(
            UserTeam.user_id == current_user.id
        )
 
        query = (
            base_query
            .where(Task.team_id.in_(subquery))
            .group_by(Task.status)
        )
 
    result = await db.execute(query)
    rows = result.all()
 
    stats = {status.name: 0 for status in TaskStatus}
 
    for status, count in rows:
        stats[status.name] = count
 
    return stats