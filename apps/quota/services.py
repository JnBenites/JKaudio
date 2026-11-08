from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import ServiceSettings
from apps.generator.models import GenerationJob


def get_service_settings():
    return ServiceSettings.get_solo()


def get_daily_usage(ip_hash):
    if not ip_hash:
        return 0

    today = timezone.localdate()

    start = timezone.make_aware(
        datetime.combine(today, time.min)
    )

    end = start + timedelta(days=1)

    return GenerationJob.objects.filter(
        ip_hash=ip_hash,
        created_at__gte=start,
        created_at__lt=end,
    ).count()


def can_generate(ip_hash):
    settings = get_service_settings()

    if settings.maintenance_mode:
        return False, 'El servicio está en mantenimiento.'

    if not settings.generation_enabled:
        return False, 'La generación está deshabilitada.'

    usage = get_daily_usage(ip_hash)

    if usage >= settings.max_generations_per_ip_per_day:
        return False, 'Has alcanzado el límite diario de generaciones.'

    return True, None
