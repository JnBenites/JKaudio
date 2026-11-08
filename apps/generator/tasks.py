
import json
import uuid
import logging
from pathlib import Path
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.generator.models import GenerationJob, GenerationEvent


logger = logging.getLogger(__name__)


def generate_audio(job_id, text, voice):
    job = GenerationJob.objects.get(pk=job_id)
    output_file = None

    try:
        job.status = GenerationJob.Status.PROCESSING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at"])

        GenerationEvent.objects.create(
            job=job,
            event_type=GenerationEvent.EventType.STARTED,
            detail="Generación iniciada."
        )

        payload = {
            "model": "kokoro",
            "input": text,
            "voice": voice,
            "response_format": "mp3",
            "stream": False,
        }

        request = Request(
            f"{settings.KOKORO_API_URL}/v1/audio/speech",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request, timeout=120) as response:
            audio_data = response.read()

        if not audio_data:
            raise RuntimeError("Kokoro devolvió un archivo vacío.")

        output_dir = Path(settings.MEDIA_ROOT) / "generated"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4().hex}.mp3"
        output_file = output_dir / filename
        output_file.write_bytes(audio_data)

        with transaction.atomic():
            job.audio_path = f"generated/{filename}"
            job.status = GenerationJob.Status.COMPLETED
            job.finished_at = timezone.now()
            job.save(update_fields=[
                "audio_path",
                "status",
                "finished_at",
            ])

            GenerationEvent.objects.create(
                job=job,
                event_type=GenerationEvent.EventType.COMPLETED,
                detail="Audio generado correctamente."
            )

        return job.audio_path

    except Exception:
        # Intentar eliminar el archivo incompleto o generado.
        # Un fallo de eliminación no debe impedir actualizar Django.
        if output_file is not None:
            try:
                if output_file.exists():
                    output_file.unlink()
            except OSError:
                logger.warning(
                    "No se pudo eliminar un archivo de audio temporal."
                )

        # Registrar el fallo independientemente de la eliminación.
        with transaction.atomic():
            job.status = GenerationJob.Status.FAILED
            job.audio_path = ""
            job.error_message = "No se pudo completar la generación."
            job.finished_at = timezone.now()
            job.save(update_fields=[
                "status",
                "audio_path",
                "error_message",
                "finished_at",
            ])

            GenerationEvent.objects.create(
                job=job,
                event_type=GenerationEvent.EventType.FAILED,
                detail="Error durante la generación."
            )

        raise
