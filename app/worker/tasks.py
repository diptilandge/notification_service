import logging
from typing import Any
from celery.exceptions import MaxRetriesExceededError

from app.worker.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.notification import Notification, NotificationStatus
from app.models.preference import UserPreference
from app.services.mock_providers import send_via_channel, DeliveryFailedException
from app.services.template_engine import render_template

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_notification(self, notification_id: str):
    logger.info(f"Processing notification: {notification_id}")
    
    db = SessionLocal()
    try:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            logger.error(f"Notification {notification_id} not found in DB.")
            return
            
        if notification.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED]:
            logger.info(f"Notification {notification_id} already processed.")
            return

        # Check user preferences
        preference = db.query(UserPreference).filter(
            UserPreference.user_id == notification.user_id,
            UserPreference.channel == notification.channel
        ).first()

        if preference and not preference.opt_in:
            logger.info(f"User {notification.user_id} opted out of {notification.channel}. Skipping.")
            notification.status = NotificationStatus.FAILED
            db.commit()
            return
        
        # Prepare message
        # If template_name is given, use it. Otherwise, assume payload is string or use JSON dump
        if notification.template_name:
            message = render_template(notification.template_name, notification.payload)
        else:
            message = str(notification.payload)
            
        # Attempt to deliver
        try:
            send_via_channel(notification.channel.value, notification.user_id, message)
            notification.status = NotificationStatus.SENT
            db.commit()
            logger.info(f"Notification {notification_id} marked as SENT.")
            
        except DeliveryFailedException as exc:
            logger.warning(f"Delivery failed for {notification_id}, retrying... ({exc})")
            
            # exponential backoff calculation (e.g. 2s, 4s, 8s)
            countdown = 2 ** self.request.retries 
            
            try:
                raise self.retry(exc=exc, countdown=countdown)
            except MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for {notification_id}. Marking as FAILED.")
                notification.status = NotificationStatus.FAILED
                db.commit()
                
    except Exception as e:
        logger.exception(f"Unexpected error processing notification {notification_id}: {e}")
        db.rollback()
        raise
    finally:
        db.close()
