from pydantic import BaseModel,model_validator,field_validator,Field
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
        return self
class TaskCreateRes(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    created_by: str
    assigned_to: Optional[str] = None
    teams_id: Optional[uuid.UUID] = None

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

class AssignTeamSchema(BaseModel):
    team_id: uuid.UUID
class AssignUserSchema(BaseModel):
    assignee_id: uuid.UUID

class TaskUniversalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    team_id: Optional[uuid.UUID] = None
    assignee_id: Optional[uuid.UUID] = None
class TaskDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    created_by: str
    team_id: Optional[uuid.UUID] = None
    assigned_to: Optional[str] = None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus

class UpdateTask(BaseModel):
    task_id:uuid.UUID
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    assignee_id: Optional[uuid.UUID] = None
 
 
class TaskBulkCreate(BaseModel):
    tasks: List[TaskCreate] = Field(..., min_length=1)
 
    @field_validator("tasks")
    def check_max_batch_size(cls, v: List[TaskCreate]) -> List[TaskCreate]:
        if len(v) > 50:
            raise ValueError("Bulk create limit is 50 tasks per request")
        return v
 
 
class TaskBulkDelete(BaseModel):
    task_ids: List[uuid.UUID] = Field(..., min_length=1)
 
    @field_validator("task_ids")
    def check_max_batch_size(cls, v: List[uuid.UUID]) -> List[uuid.UUID]:
        if len(v) > 50:
            raise ValueError("Bulk delete limit is 50 tasks per request")
        return v