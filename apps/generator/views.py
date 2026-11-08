import logging
from datetime import timedelta
from pathlib import Path

from apps.generator.voices import VOICES, DEFAULT_VOICE

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.quota.models import ServiceSettings
from apps.quota.services import can_generate
from apps.quota.security import get_request_ip_hash

from apps.generator.models import GenerationJob, GenerationEvent
from apps.generator.queue import get_generation_queue
from apps.generator.tasks import generate_audio


logger = logging.getLogger(__name__)


AVAILABLE_VOICES = {
    'af_alloy',
    'af_amelia_inno',
    'af_aoede',
    'af_bella',
    'af_goodall_inno',
    'af_heart',
    'af_jadzia',
    'af_jessica',
    'af_kore',
    'af_nicole',
    'af_nova',
    'af_river',
    'af_sarah',
    'af_sky',
    'af_v0',
    'af_v0bella',
    'af_v0irulan',
    'af_v0nicole',
    'af_v0sarah',
    'af_v0sky',
    'am_adam',
    'am_echo',
    'am_eric',
    'am_fenrir',
    'am_liam',
    'am_michael',
    'am_onyx',
    'am_price_inno',
    'am_puck',
    'am_santa',
    'am_v0adam',
    'am_v0gurney',
    'am_v0michael',
    'bf_alice',
    'bf_emma',
    'bf_isabella',
    'bf_lily',
    'bf_v0emma',
    'bf_v0isabella',
    'bm_atten_inno',
    'bm_daniel',
    'bm_fable',
    'bm_george',
    'bm_lewis',
    'bm_v0george',
    'bm_v0lewis',
    'ef_dora',
    'em_alex',
    'em_santa',
    'ff_siwis',
    'hf_alpha',
    'hf_beta',
    'hm_omega',
    'hm_psi',
    'if_sara',
    'im_nicola',
    'jf_alpha',
    'jf_gongitsune',
    'jf_nezumi',
    'jf_tebukuro',
    'jm_kumo',
    'pf_dora',
    'pm_alex',
    'pm_santa',
    'zf_xiaobei',
    'zf_xiaoni',
    'zf_xiaoxiao',
    'zf_xiaoyi',
    'zm_yunjian',
    'zm_yunxi',
    'zm_yunxia',
    'zm_yunyang',
}


def home(request):
    jobs = []

    if request.user.is_authenticated:
        jobs = list(
            GenerationJob.objects.filter(
                user=request.user,
                status=GenerationJob.Status.COMPLETED,
                audio_path__gt=''
            ).order_by('-created_at')[:10]
        )

        for job in jobs:
            if check_job_expiration(job):
                job.refresh_from_db()

        jobs = [
            job for job in jobs
            if job.status == GenerationJob.Status.COMPLETED
            and job.audio_path
        ]

    return render(request, 'home.html', {
        'history_jobs': jobs,
        'voices': VOICES,
        'default_voice': DEFAULT_VOICE,
    })


def get_audio_file(job):
    if not job.audio_path:
        raise Http404("Audio no disponible.")

    media_root = Path(settings.MEDIA_ROOT).resolve()
    generated_root = (media_root / "generated").resolve()
    audio_file = (media_root / job.audio_path).resolve()

    if generated_root not in audio_file.parents:
        raise Http404("Ruta de audio no válida.")

    return audio_file


def expire_job(job, detail="Audio eliminado por vencimiento."):
    try:
        audio_file = get_audio_file(job)

        if audio_file.exists():
            audio_file.unlink()

    except Http404:
        pass

    except OSError:
        return False

    job.status = GenerationJob.Status.EXPIRED
    job.audio_path = ""

    job.save(update_fields=[
        "status",
        "audio_path",
    ])

    GenerationEvent.objects.create(
        job=job,
        event_type=GenerationEvent.EventType.EXPIRED,
        detail=detail
    )

    return True


def check_job_expiration(job):
    if job.status != GenerationJob.Status.COMPLETED:
        return False

    retention = ServiceSettings.get_solo().audio_retention_minutes

    if not job.finished_at:
        expire_job(
            job,
            "Audio sin fecha de finalización."
        )
        return True

    expiration_time = job.finished_at + timedelta(minutes=retention)

    if timezone.now() >= expiration_time:
        expire_job(job)
        return True

    try:
        audio_file = get_audio_file(job)

    except Http404:
        expire_job(
            job,
            "Archivo de audio no encontrado."
        )
        return True

    if not audio_file.is_file():
        expire_job(
            job,
            "Archivo de audio no encontrado."
        )
        return True

    return False


@login_required
@require_POST
def validate_generation(request):
    text = request.POST.get('text', '').strip()
    voice = request.POST.get('voice', 'ef_dora').strip()

    if not text:
        return JsonResponse({
            'success': False,
            'message': 'Escribe un texto para continuar.'
        }, status=400)

    service_settings = ServiceSettings.get_solo()

    if len(text) > service_settings.max_text_length:
        return JsonResponse({
            'success': False,
            'message': (
                f'El máximo permitido es '
                f'{service_settings.max_text_length} caracteres.'
            )
        }, status=400)

    if voice not in AVAILABLE_VOICES:
        return JsonResponse({
            'success': False,
            'message': 'La voz seleccionada no está disponible.'
        }, status=400)

    ip_hash = get_request_ip_hash(request)
    allowed, message = can_generate(ip_hash)

    if not allowed:
        return JsonResponse({
            'success': False,
            'message': message
        }, status=429)

    job = GenerationJob.objects.create(
        user=request.user,
        ip_hash=ip_hash,
        status=GenerationJob.Status.QUEUED
    )

    GenerationEvent.objects.create(
        job=job,
        event_type=GenerationEvent.EventType.REQUESTED,
        detail='Solicitud recibida.'
    )

    try:
        queue = get_generation_queue()

        queue.enqueue(
            generate_audio,
            job.id,
            text,
            voice,
            job_timeout=600,
            result_ttl=0,
            failure_ttl=0,
        )

        GenerationEvent.objects.create(
            job=job,
            event_type=GenerationEvent.EventType.QUEUED,
            detail='Trabajo agregado a Redis.'
        )

    except Exception:
        logger.exception(
            "No se pudo enviar la generación a Redis. Job ID: %s",
            job.id
        )

        job.status = GenerationJob.Status.FAILED
        job.error_message = 'No se pudo enviar el trabajo a la cola.'
        job.finished_at = timezone.now()

        job.save(update_fields=[
            'status',
            'error_message',
            'finished_at',
        ])

        GenerationEvent.objects.create(
            job=job,
            event_type=GenerationEvent.EventType.FAILED,
            detail='Error al enviar el trabajo a Redis.'
        )

        return JsonResponse({
            'success': False,
            'message': (
                'No se pudo iniciar la generación. '
                'Inténtalo nuevamente.'
            )
        }, status=503)

    return JsonResponse({
        'success': True,
        'message': 'Audio agregado a la cola.',
        'job_id': job.id,
        'status': job.status,
        'characters': len(text)
    })


@login_required
@require_GET
def job_status(request, job_id):
    job = get_object_or_404(
        GenerationJob,
        pk=job_id,
        user=request.user
    )

    check_job_expiration(job)

    message = {
        GenerationJob.Status.QUEUED: 'Tu audio está en cola.',
        GenerationJob.Status.PROCESSING: 'Generando tu audio.',
        GenerationJob.Status.COMPLETED: 'Audio generado correctamente.',
        GenerationJob.Status.FAILED: (
            job.error_message or 'No se pudo generar el audio.'
        ),
        GenerationJob.Status.CANCELLED: 'La generación fue cancelada.',
        GenerationJob.Status.EXPIRED: 'El audio ha vencido.',
    }.get(job.status, 'Estado desconocido.')

    audio_url = None
    download_url = None

    if job.status == GenerationJob.Status.COMPLETED:
        audio_url = reverse(
            'generator:stream_audio',
            args=[job.id]
        )

        download_url = reverse(
            'generator:download_audio',
            args=[job.id]
        )

    return JsonResponse({
        'success': True,
        'status': job.status,
        'message': message,
        'audio_url': audio_url,
        'download_url': download_url,
    })


@login_required
@require_GET
def download_audio(request, job_id):
    job = get_object_or_404(
        GenerationJob,
        pk=job_id,
        user=request.user
    )

    if check_job_expiration(job):
        raise Http404("El audio ha vencido.")

    if job.status != GenerationJob.Status.COMPLETED:
        raise Http404("El audio todavía no está disponible.")

    audio_file = get_audio_file(job)

    if not audio_file.is_file():
        expire_job(
            job,
            "Archivo de audio no encontrado durante la descarga."
        )
        raise Http404("Archivo de audio no encontrado.")

    try:
        file_handle = audio_file.open('rb')
    except OSError:
        raise Http404("No se pudo abrir el audio.")

    now = timezone.now()

    GenerationJob.objects.filter(pk=job.pk).update(
        download_count=F('download_count') + 1,
        downloaded=True,
        downloaded_at=now
    )

    GenerationEvent.objects.create(
        job=job,
        event_type=GenerationEvent.EventType.DOWNLOADED,
        detail='Audio descargado.'
    )

    return FileResponse(
        file_handle,
        as_attachment=True,
        filename=audio_file.name
    )


@login_required
@require_GET
def stream_audio(request, job_id):
    job = get_object_or_404(
        GenerationJob,
        pk=job_id,
        user=request.user
    )

    if check_job_expiration(job):
        raise Http404("El audio ha vencido.")

    if job.status != GenerationJob.Status.COMPLETED:
        raise Http404("El audio todavía no está disponible.")

    audio_file = get_audio_file(job)

    if not audio_file.is_file():
        expire_job(
            job,
            "Archivo de audio no encontrado durante la reproducción."
        )
        raise Http404("Archivo de audio no encontrado.")

    try:
        file_handle = audio_file.open('rb')
    except OSError:
        raise Http404("No se pudo abrir el audio.")

    return FileResponse(
        file_handle,
        as_attachment=False,
        filename=audio_file.name
    )