from pydantic import BaseModel
import uuid
from datetime import datetime

class ActivityLogRes(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action_type: str
    resource_type: str
    timestamp: datetime