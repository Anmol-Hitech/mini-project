from pydantic import BaseModel,model_validator
from typing import List,Optional
import uuid
from models.tasks import TaskPriority,TaskStatus
class TaskCreate(BaseModel):
    title:str
    description:Optional[str]=None
    priority:Optional[str]=None
    status:Optional[str]=None
    assignee_id: Optional[uuid.UUID] = None
    @model_validator(mode="after")
    def validate_fields(self):
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")
class TaskCreateRes(BaseModel):
    title:str
    description:str
    priority:str
    status:str
    created_by:str
    assigned_to:str
    teams_id:uuid.UUID


class BulkTaskCreate(BaseModel):
    tasks: List[TaskCreate]

class TaskStats(BaseModel):
    todo:int
    doing:int
    done:int
    total:int

class TaskStatsPriority(BaseModel):
    low:int
    medium:int
    high:int
    total:int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    assignee_id: Optional[uuid.UUID] = None

