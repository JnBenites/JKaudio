
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone

from rq import Worker

from apps.generator.models import GenerationJob, GenerationEvent
from apps.generator.queue import get_generation_queue
from apps.quota.models import ServiceSettings


@staff_member_required
def monitoring(request):
    today = timezone.localdate()

    # Estado de las generaciones en la base de datos.
    job_counts = {
        status: GenerationJob.objects.filter(status=status).count()
        for status, label in GenerationJob.Status.choices
    }

    # Actividad registrada durante el día.
    requests_today = GenerationEvent.objects.filter(
        event_type=GenerationEvent.EventType.REQUESTED,
        created_at__date=today,
    ).count()

    downloads_today = GenerationEvent.objects.filter(
        event_type=GenerationEvent.EventType.DOWNLOADED,
        created_at__date=today,
    ).count()

    # Últimos trabajos registrados.
    recent_jobs = GenerationJob.objects.select_related(
        'user'
    ).order_by('-created_at')[:10]

    # Configuración del servicio.
    service_settings = ServiceSettings.objects.filter(pk=1).first()

    # Información inicial de Redis y RQ.
    redis_data = {
        'connected': False,
        'queue_name': '',
        'pending': 0,
        'processing': 0,
        'workers': [],
        'failed': 0,
        'finished': 0,
        'error': None,
    }

    try:
        queue = get_generation_queue()
        connection = queue.connection

        # Comprobar conexión con Redis.
        connection.ping()

        # Obtener trabajadores registrados en RQ.
        workers = Worker.all(connection=connection)

        worker_data = []

        for worker in workers:
            worker_data.append({
                'name': worker.name,
                'state': worker.get_state(),
            })

        # Actualizar información de la cola.
        redis_data.update({
            'connected': True,
            'queue_name': queue.name,
            'pending': queue.count,
            'processing': queue.started_job_registry.count,
            'workers': worker_data,
            'failed': queue.failed_job_registry.count,
            'finished': queue.finished_job_registry.count,
        })

    except Exception:
        redis_data['error'] = (
            'No fue posible consultar Redis o la cola de trabajos.'
        )

    context = {
        'today': today,
        'job_counts': job_counts,
        'requests_today': requests_today,
        'downloads_today': downloads_today,
        'recent_jobs': recent_jobs,
        'service_settings': service_settings,
        'redis_data': redis_data,
    }

    return render(
        request,
        'operations/monitoring.html',
        context,
    )
