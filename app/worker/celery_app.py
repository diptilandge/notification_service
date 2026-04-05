from celery import Celery
from kombu import Queue, Exchange
from app.core.config import settings

celery_app = Celery(
    "notification_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.worker.tasks']
)

# Configure Queues for different priorities
celery_app.conf.task_queues = (
    Queue('critical', Exchange('critical'), routing_key='critical'),
    Queue('high', Exchange('high'), routing_key='high'),
    Queue('normal', Exchange('normal'), routing_key='normal'),
    Queue('low', Exchange('low'), routing_key='low'),
)

celery_app.conf.task_routes = {
    'app.worker.tasks.process_notification': {
        'queue': 'normal', # default, overridden when calling apply_async
    }
}

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
