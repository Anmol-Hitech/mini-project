import bcrypt
from datetime import datetime,timedelta,timezone
from jose import jwt
from config import settings
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException
from sqlalchemy.orm import Session
from jose import JWTError
from models import User
from config.database import get_db
from sqlalchemy import select

def create_access_token(data:dict):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)

def hash_password(password:str):
    salt=bcrypt.gensalt()
    hashed_password=bcrypt.hashpw(password.encode("utf-8"),salt)
    return hashed_password.decode("utf-8")

def verify_password(plain_password:str,hashed_password:str):
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),hashed_password.encode("utf-8")
    )
