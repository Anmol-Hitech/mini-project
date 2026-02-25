from fastapi import APIRouter, Depends, HTTPException,BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import uuid
from auth.auth import generate_token,decode_invite_token
from config.database import get_db
from auth.dependency import get_current_user
from models.invite_token import InviteToken
from models.teams import Teams,UserTeam
from models.users import User, RoleEnum
from schemas.invitetoken import InviteCreate,InviteRead
from utils.email_send import send_invite_email
inviterouter = APIRouter()


@inviterouter.post("/create-invite", response_model=InviteRead)
async def create_invite_token(
    data: InviteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.MANAGER:
        raise HTTPException(status_code=403, detail="Only manager can create invite token")

    result = await db.execute(select(Teams).where(Teams.id==data.team_id))
    team=result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only create invite for your own team")

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    token = await generate_token({"sub": str(data.team_id)})
    invite = InviteToken(
        id=uuid.uuid4(),
        token=token,
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


@inviterouter.post("/send-invite/{invite_id}/{user_id}")
async def send_invite_email_api(
    invite_id: uuid.UUID,
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(InviteToken).where(InviteToken.id == invite_id)
    )
    invite = result.scalars().first()

    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    if invite.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only send your own invite")

    if invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite token expired")

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    target_user = result.scalars().first()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(Teams).where(Teams.id == invite.team_id)
    )
    team = result.scalars().first()

    background_tasks.add_task(
        send_invite_email,
        target_user.email,
        team.name,
        invite.token
    )

    print(f"DEBUG: Invite for {team.name} sent {invite.token}")

    return {"message": "Invite email sent successfully"}

@inviterouter.post("/join-team/{token}")
async def join_team(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payload = decode_invite_token(token)

    team_id = payload.get("sub")

    if not team_id:
        raise HTTPException(status_code=400, detail="Invalid invite token")

    result = await db.execute(
        select(InviteToken).where(InviteToken.token == token)
    )
    invite = result.scalars().first()

    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    if invite.is_used:
        raise HTTPException(status_code=400, detail="Invite already used")

    if invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite token expired")

    result = await db.execute(
        select(UserTeam).where(
            UserTeam.user_id == current_user.id,
            UserTeam.team_id == invite.team_id
        )
    )
    existing_membership = result.scalars().first()

    if existing_membership:
        raise HTTPException(status_code=400, detail="Already a team member")

    new_membership = UserTeam(
        user_id=current_user.id,
        team_id=invite.team_id,
        joined_at=datetime.now(timezone.utc)
    )

    db.add(new_membership)

    invite.is_used = True

    await db.commit()

    return {"message": "Successfully joined the team"}