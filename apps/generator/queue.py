from django.conf import settings
from redis import Redis
from rq import Queue


def get_redis_connection():
    if not settings.REDIS_URL:
        raise RuntimeError("REDIS_URL no está configurada.")

    return Redis.from_url(settings.REDIS_URL)


def get_generation_queue():
    connection = get_redis_connection()

    return Queue(
        settings.RQ_QUEUE_NAME,
        connection=connection,
        default_timeout=settings.RQ_JOB_TIMEOUT,
    )