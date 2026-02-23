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
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="login")
async def get_current_user(
    token:str = Depends(oauth2_scheme),db:Session=Depends(get_db)
):
    try:
        payload=jwt.decode(
            token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM]
        )
        email=payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401,detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401,detail="Invalid token")
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400,detail="Not found")
    
    return user

def role_required(required_role: str,current_user: User = Depends(get_current_user)):
    if current_user.role != required_role:
        raise HTTPException(status_code=403, detail="Access Denied")
    return current_user