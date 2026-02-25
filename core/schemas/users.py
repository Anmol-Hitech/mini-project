from pydantic import BaseModel,EmailStr,model_validator
from typing import List,Optional,Literal
from fastapi import HTTPException
from models.users import RoleEnum
import uuid
import re
class CreateUser(BaseModel):
    name:str
    email:EmailStr
    password:str
    role:str
    @model_validator(mode="after")
    def validate_fields(self):
        if not self.name or not self.name.strip():
            raise HTTPException(status_code=400,detail="Name cannot be empty")

        password = self.password

        if len(password) < 8:
            raise HTTPException(status_code=400,detail="Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", password):
            raise HTTPException(status_code=400,detail="Password must contain at least one uppercase letter")

        if not re.search(r"\d", password):
            raise HTTPException(status_code=400,detail="Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise HTTPException(status_code=400,detail="Password must contain at least one special character")

        return self

class CreateUserResponse(BaseModel):
    name:str
    email:EmailStr
    role:str
    is_active:bool

class LoginUser(BaseModel):
    email:EmailStr
    password:str
    name:str
    role:Literal["admin","manager","employee"]

class UpdateUser(BaseModel):
    email:Optional[EmailStr]=None
    name:Optional[str]=None

class UserListResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: RoleEnum
    is_active: bool    

class PromoteEmp(BaseModel):
    team_name:Optional[str]=None
class TeamRead(BaseModel):
    id:uuid.UUID
    name:str
    created_by_id:uuid.UUID
    is_deleted:bool