from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.database import get_db
from auth.auth import hash_password,verify_password,create_access_token
from auth.dependency import get_current_user
from schemas.users import CreateUser, CreateUserResponse,LoginUser
from models.users import User, RoleEnum
import uuid

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

    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}
