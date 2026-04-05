from sqlalchemy import Column, String, Boolean, Enum
from app.db.session import Base
from app.models.notification import NotificationChannel

class UserPreference(Base):
    __tablename__ = "user_preferences"

    # In a real system, you might have a composite primary key or a separate id.
    # For simplicity, we can use user_id + channel as composite approach 
    # but here let's just make user_id and channel indexed and uniquely constrained, 
    # or just use an id. Let's use user_id and channel as composite primary key.
    
    user_id = Column(String, primary_key=True)
    channel = Column(Enum(NotificationChannel), primary_key=True)
    opt_in = Column(Boolean, nullable=False, default=True)
