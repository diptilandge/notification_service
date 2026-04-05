import redis
from fastapi import HTTPException
from app.core.config import settings
import time

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class RateLimitExceeded(Exception):
    pass

def check_rate_limit(user_id: str):
    """
    Implements a simple fixed window rate limiter per user per hour.
    """
    current_hour = int(time.time() / 3600)
    key = f"rate_limit:{user_id}:{current_hour}"
    
    # Increment the counter
    count = redis_client.incr(key)
    if count == 1:
        # Set expiry for a bit more than an hour
        redis_client.expire(key, 3600 + 60)
        
    if count > settings.RATE_LIMIT_PER_USER_PER_HOUR:
        raise RateLimitExceeded("Rate limit exceeded. Maximum 100 requests per hour allowed.")
