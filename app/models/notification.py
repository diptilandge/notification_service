import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum, JSON
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class NotificationPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.NORMAL)
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    idempotency_key = Column(String, index=True, unique=True, nullable=True)
    
    # Template to use (optional, if none use raw payload logic)
    template_name = Column(String, nullable=True)
    payload = Column(JSON, nullable=False) # Variables for template or exact message body
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
