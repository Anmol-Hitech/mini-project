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