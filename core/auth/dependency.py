from datetime import datetime, timezone
import jwt
from jwt import PyJWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.config import settings
from config.database import get_db
from models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        email: str | None = payload.get("sub")

        if email is None:
            raise credentials_exception

    except PyJWTError:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user
def require_roles(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Abey! {current_user.role} allowed nahi h. Only {allowed_roles} can enter.",
            )
        return current_user
 
    return role_checker