"""Business rules and Supabase data access for task operations."""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from supabase import Client

from .models import CurrentUser, TaskCreate, TaskStatus, TaskStatusUpdate


class TaskService:
    def __init__(self, client: Client):
        self.client = client

    def current_user(self, access_token: str) -> CurrentUser:
        try:
            auth_user = self.client.auth.get_user(access_token).user
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid or expired access token") from exc
        if auth_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid or expired access token")

        result = (self.client.table("users")
                  .select("id, company_id, role")
                  .eq("auth_user_id", auth_user.id)
                  .single()
                  .execute())
        if not result.data:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="No application profile was found")
        return CurrentUser(id=result.data["id"], company_id=result.data["company_id"],
                           role=result.data["role"])

    def create_task(self, task: TaskCreate, actor: CurrentUser) -> dict[str, Any]:
        if actor.role != "manager":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Only managers can create tasks")

        assignee = (self.client.table("users").select("id")
                    .eq("id", str(task.assigned_to))
                    .eq("company_id", str(actor.company_id)).execute())
        if not assignee.data:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Assignee must belong to your company")

        payload = task.model_dump(mode="json")
        payload.update({"company_id": str(actor.company_id), "created_by": str(actor.id)})
        return self.client.table("tasks").insert(payload).execute().data[0]

    def list_tasks(self, actor: CurrentUser) -> list[dict[str, Any]]:
        # company_id comes from the verified profile, never from a query parameter.
        return (self.client.table("tasks").select("*")
                .eq("company_id", str(actor.company_id))
                .order("created_at", desc=True).execute().data)

    def update_status(self, task_id: UUID, update: TaskStatusUpdate,
                      actor: CurrentUser) -> dict[str, Any]:
        task_result = (self.client.table("tasks").select("*").eq("id", str(task_id))
                       .eq("company_id", str(actor.company_id)).maybe_single().execute())
        task = task_result.data
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        if actor.role != "manager" and task["assigned_to"] != str(actor.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You can update only tasks assigned to you")
        return (self.client.table("tasks").update({"status": update.status.value})
                .eq("id", str(task_id)).eq("company_id", str(actor.company_id))
                .execute().data[0])
