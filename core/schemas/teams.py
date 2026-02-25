from pydantic import BaseModel,model_validator
from typing import List,Optional
import uuid
class TeamsCreate(BaseModel):
    name:str
    @model_validator(mode="after")
    def validate_fields(self):
        if not self.name or not self.name.strip():
            raise ValueError("Name cannot be empty")
        return self
class TeamsCreateResponse(BaseModel):
    name:str
    created_by:str
class AssignTeamRequest(BaseModel):
    user_id: uuid.UUID
    team_id: uuid.UUID
class GetTeam(BaseModel):
    team_id: uuid.UUID
    name:str
    created_by_id:uuid.UUID
    is_deleted:bool

class TeamMemberStats(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    task_count: int
 
 
class ManagerDetails(BaseModel):
    id: uuid.UUID
    name: str
    email: str
 
 
class TeamDetailResponse(BaseModel):
    team_id: uuid.UUID
    team_name: str
    task_count: int
    member_count: int
    manager: ManagerDetails
    members: List[TeamMemberStats]

class TeamRead(BaseModel):
    id:uuid.UUID
    name:str
    created_by_id:uuid.UUID
    is_deleted:bool