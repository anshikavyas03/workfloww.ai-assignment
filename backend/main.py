import os
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client

from .models import CurrentUser, TaskCreate, TaskResponse, TaskStatusUpdate
from .service import TaskService

app = FastAPI(title="Multi-Tenant Task Management API", version="1.0.0")
bearer_scheme = HTTPBearer(auto_error=False)


def get_task_service() -> TaskService:
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured")
    return TaskService(create_client(url, service_key))


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    service: TaskService = Depends(get_task_service),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="A Bearer access token is required")
    return service.current_user(credentials.credentials)


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, actor: CurrentUser = Depends(get_current_user),
                service: TaskService = Depends(get_task_service)):
    return service.create_task(task, actor)


@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(actor: CurrentUser = Depends(get_current_user),
              service: TaskService = Depends(get_task_service)):
    return service.list_tasks(actor)


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task_status(task_id: UUID, update: TaskStatusUpdate,
                       actor: CurrentUser = Depends(get_current_user),
                       service: TaskService = Depends(get_task_service)):
    return service.update_status(task_id, update, actor)
