from pydantic import BaseModel,EmailStr
from typing import List,Optional

class CreateUser(BaseModel):
    name:str
    email:EmailStr
    password:str
    role:str

class CreateUserResponse(BaseModel):
    name:str
    email:EmailStr
    role:str
    is_active:bool
