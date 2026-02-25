from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import uuid

from config.database import get_db
from auth.dependency import get_current_user
from models.invite_token import InviteToken
from models.teams import Teams
from models.users import User, RoleEnum
from schemas.invitetoken import InviteCreate,InviteRead

inviterouter = APIRouter()


@inviterouter.post("/create-invite", response_model=InviteRead)
async def create_invite_token(
    data: InviteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.MANAGER:
        raise HTTPException(status_code=403, detail="Only manager can create invite token")

    team = await db.get(Teams, data.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only create invite for your own team")

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    invite = InviteToken(
        id=uuid.uuid4(),
        team_id=data.team_id,
        created_by_id=current_user.id,
        expires_at=expires_at,
        is_used=False
    )

    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    return {
        "token_id": invite.id,
        "team_id": invite.team_id,
        "expires_at": invite.expires_at,
        "is_used":invite.is_used
    }