from pydantic import BaseModel,model_validator
from typing import List,Optional
import uuid
class TeamsCreate(BaseModel):
    name:str
    @model_validator(mode="after")
    def validate_fields(self):
        if not self.name or not self.name.strip():
            raise ValueError("Name cannot be empty")

class TeamsCreateResponse( BaseModel):
    name:str
    created_by:str