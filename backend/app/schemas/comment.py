"""API schemas for comments.

Comments belong to a task and have an author (a user). Comments are
relatively simple: just text, timestamps, and relationships to task and user.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    body: str = Field(min_length=1)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    body: str
    task_id: uuid.UUID
    author_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
