"""Task endpoints.

Tasks are nested under projects: /projects/{project_id}/tasks. Every endpoint
requires authentication and enforces that the user can only access tasks in
their own organization's projects.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_task_service
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task import TaskService

router = APIRouter(tags=["tasks"])


@router.post("/projects/{project_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: uuid.UUID,
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    task = service.create(current_user, project_id, data)
    return TaskRead.model_validate(task)


@router.get("/projects/{project_id}/tasks", response_model=list[TaskRead])
def list_tasks(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> list[TaskRead]:
    tasks = service.list(current_user, project_id, limit=limit, offset=offset)
    return [TaskRead.model_validate(t) for t in tasks]


@router.get("/projects/{project_id}/tasks/{task_id}", response_model=TaskRead)
def get_task(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    task = service.get(current_user, project_id, task_id)
    return TaskRead.model_validate(task)


@router.patch("/projects/{project_id}/tasks/{task_id}", response_model=TaskRead)
def update_task(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    task = service.update(current_user, project_id, task_id, data)
    return TaskRead.model_validate(task)


@router.delete("/projects/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> None:
    service.delete(current_user, project_id, task_id)
