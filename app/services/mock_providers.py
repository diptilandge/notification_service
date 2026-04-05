import logging
import random
import time

logger = logging.getLogger(__name__)

class DeliveryFailedException(Exception):
    pass

def send_email(user_id: str, message: str):
    logger.info(f"Attempting to send EMAIL to {user_id}")
    _simulate_delivery()
    logger.info(f"Successfully sent EMAIL to {user_id}")

def send_sms(user_id: str, message: str):
    logger.info(f"Attempting to send SMS to {user_id}")
    _simulate_delivery()
    logger.info(f"Successfully sent SMS to {user_id}")

def send_push(user_id: str, message: str):
    logger.info(f"Attempting to send PUSH to {user_id}")
    _simulate_delivery()
    logger.info(f"Successfully sent PUSH to {user_id}")

def _simulate_delivery():
    # Simulate network delay
    time.sleep(random.uniform(0.1, 0.5))
    
    # 10% chance of random failure to demonstrate retries
    if random.random() < 0.1:
        raise DeliveryFailedException("Random provider network error")

def send_via_channel(channel: str, user_id: str, message: str):
    if channel.lower() == "email":
        send_email(user_id, message)
    elif channel.lower() == "sms":
        send_sms(user_id, message)
    elif channel.lower() == "push":
        send_push(user_id, message)
    else:
        raise ValueError(f"Unknown channel: {channel}")
