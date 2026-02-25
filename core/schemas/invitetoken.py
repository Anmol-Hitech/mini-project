from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class InviteCreate(BaseModel):
    team_id: UUID

class InviteRead(BaseModel):
    token_id: UUID
    team_id: UUID
    expires_at: datetime
    is_used: bool