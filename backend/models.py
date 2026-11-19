from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CurrentUser(BaseModel):
    id: UUID
    company_id: UUID
    role: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2_000)
    assigned_to: UUID
    due_date: Optional[date] = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskResponse(BaseModel):
    id: UUID
    company_id: UUID
    assigned_to: UUID
    created_by: UUID
    title: str
    description: str
    status: TaskStatus
    due_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
