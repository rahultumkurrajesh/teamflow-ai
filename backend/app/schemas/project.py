"""API schemas for projects.

Projects belong to an organization and have many tasks. Input schemas
(Create, Update) never include timestamps or IDs; output schemas (Read)
include them so clients know what they're working with.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
