from datetime import datetime, timedelta, timezone
import jwt

from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from config.config import settings
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import User
from config.database import get_db
from sqlalchemy import select
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False
    
async def generate_token(data:dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.INVITE_TOKEN_EXPIRE_TIME
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.INVITE_KEY,
        algorithm=settings.ALGORITHM
    )

def decode_invite_token(token:dict):
    try:
        payload = jwt.decode(
            token,
            settings.INVITE_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired invite token")