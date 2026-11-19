from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.models import TaskCreate, TaskStatus, TaskStatusUpdate


def test_task_create_rejects_a_blank_title():
    with pytest.raises(ValidationError):
        TaskCreate(title="", assigned_to=uuid4())


def test_status_update_only_accepts_known_statuses():
    assert TaskStatusUpdate(status="completed").status is TaskStatus.COMPLETED
    with pytest.raises(ValidationError):
        TaskStatusUpdate(status="done")
