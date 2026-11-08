
from django.db import transaction
from django.utils import timezone

from rq.exceptions import AbandonedJobError

from apps.generator.models import GenerationJob, GenerationEvent


def handle_abandoned_generation(
    rq_job,
    exc_type,
    exc_value,
    traceback_obj
):
    """
    Sincroniza Django cuando RQ detecta un trabajo abandonado.

    No registra ni almacena el texto enviado para generar el audio.
    """

    if not issubclass(exc_type, AbandonedJobError):
        return True

    # Si RQ tiene reintentos pendientes, no declarar fallida
    # la generación de Django todavía.
    retries_left = getattr(rq_job, "retries_left", None)

    if retries_left is not None and retries_left > 0:
        return True

    try:
        # El primer argumento es el ID de GenerationJob.
        # No utilizamos ni registramos los demás argumentos.
        django_job_id = rq_job.args[0]

    except (IndexError, TypeError):
        return True

    with transaction.atomic():
        updated = GenerationJob.objects.filter(
            pk=django_job_id,
            status__in=[
                GenerationJob.Status.QUEUED,
                GenerationJob.Status.PROCESSING,
            ]
        ).update(
            status=GenerationJob.Status.FAILED,
            error_message="El proceso de generación fue interrumpido.",
            finished_at=timezone.now()
        )

        if updated:
            GenerationEvent.objects.create(
                job_id=django_job_id,
                event_type=GenerationEvent.EventType.FAILED,
                detail="Generación interrumpida por abandono del trabajador RQ."
            )

    return True
