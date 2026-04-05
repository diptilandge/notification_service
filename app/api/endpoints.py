from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.db.session import get_db
from app.models.notification import Notification, NotificationStatus
from app.models.preference import UserPreference
from app.schemas.schemas import (
    NotificationRequest,
    NotificationResponse,
    UserPreferenceUpdate,
    UserPreferenceResponse
)
from app.worker.tasks import process_notification
from app.services.rate_limiter import check_rate_limit, RateLimitExceeded

router = APIRouter()

@router.post("/notifications", response_model=NotificationResponse, status_code=status.HTTP_202_ACCEPTED)
def send_notification(request: NotificationRequest, db: Session = Depends(get_db)):
    try:
        check_rate_limit(request.user_id)
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))

    # Idempotency check
    if request.idempotency_key:
        existing = db.query(Notification).filter(Notification.idempotency_key == request.idempotency_key).first()
        if existing:
            return existing

    # Create notification record
    notif = Notification(
        id=str(uuid.uuid4()),
        user_id=request.user_id,
        channel=request.channel,
        priority=request.priority,
        status=NotificationStatus.PENDING,
        idempotency_key=request.idempotency_key,
        template_name=request.template_name,
        payload=request.payload
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    # Queue task with celery mapping to priority
    queue_name = request.priority.value
    process_notification.apply_async(args=[notif.id], queue=queue_name)

    return notif

@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: str, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif

@router.get("/users/{user_id}/notifications", response_model=List[NotificationResponse])
def get_user_notifications(user_id: str, db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    return notifs

@router.post("/users/{user_id}/preferences", response_model=UserPreferenceResponse)
def set_user_preference(user_id: str, preference: UserPreferenceUpdate, db: Session = Depends(get_db)):
    pref = db.query(UserPreference).filter(
        UserPreference.user_id == user_id, 
        UserPreference.channel == preference.channel
    ).first()
    
    if pref:
        pref.opt_in = preference.opt_in
    else:
        pref = UserPreference(
            user_id=user_id,
            channel=preference.channel,
            opt_in=preference.opt_in
        )
        db.add(pref)
        
    db.commit()
    db.refresh(pref)
    return pref

@router.get("/users/{user_id}/preferences", response_model=List[UserPreferenceResponse])
def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).all()
    return prefs
