from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.notification import NotificationChannel, NotificationPriority, NotificationStatus

# Notification Schemas
class NotificationRequest(BaseModel):
    user_id: str
    channel: NotificationChannel
    priority: NotificationPriority = NotificationPriority.NORMAL
    idempotency_key: Optional[str] = None
    template_name: Optional[str] = None
    payload: Dict[str, Any]

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    channel: NotificationChannel
    priority: NotificationPriority
    status: NotificationStatus
    idempotency_key: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Preference Schemas
class UserPreferenceUpdate(BaseModel):
    channel: NotificationChannel
    opt_in: bool

class UserPreferenceResponse(BaseModel):
    user_id: str
    channel: NotificationChannel
    opt_in: bool

    class Config:
        from_attributes = True
