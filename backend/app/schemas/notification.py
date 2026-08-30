"""API schemas for notifications.

Notifications are read-only from the API perspective (created only by workers).
This schema is used to return notifications in responses.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    message: str
    is_read: bool
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
