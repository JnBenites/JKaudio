
from django.core.management.base import BaseCommand
from django.db import transaction
from django.http import Http404
from django.utils import timezone

from apps.generator.models import GenerationJob, GenerationEvent
from apps.generator.views import get_audio_file
from apps.quota.models import ServiceSettings


class Command(BaseCommand):
    help = "Elimina los audios que hayan superado su tiempo de retención."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula la limpieza sin modificar archivos ni registros."
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        retention = ServiceSettings.get_solo().audio_retention_minutes
        expiration_limit = timezone.now() - timezone.timedelta(
            minutes=retention
        )

        jobs = GenerationJob.objects.filter(
            status=GenerationJob.Status.COMPLETED,
            finished_at__lte=expiration_limit
        )

        candidates = 0
        deleted = 0
        errors = 0

        self.stdout.write(
            f"Retención configurada: {retention} minutos."
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("MODO SIMULACIÓN: no se borrará nada.")
            )

        for job in jobs.iterator():
            try:
                audio_file = get_audio_file(job)

                if dry_run:
                    candidates += 1
                    self.stdout.write(
                        f"[SIMULACIÓN] Trabajo #{job.pk}: {audio_file}"
                    )
                    continue

                with transaction.atomic():
                    job = GenerationJob.objects.select_for_update().get(
                        pk=job.pk
                    )

                    if job.status != GenerationJob.Status.COMPLETED:
                        continue

                    if job.finished_at and job.finished_at > expiration_limit:
                        continue

                    audio_file = get_audio_file(job)

                    if audio_file.exists():
                        audio_file.unlink()

                    job.status = GenerationJob.Status.EXPIRED
                    job.audio_path = ""
                    job.save(update_fields=["status", "audio_path"])

                    GenerationEvent.objects.create(
                        job=job,
                        event_type=GenerationEvent.EventType.EXPIRED,
                        detail="Audio eliminado automáticamente por vencimiento."
                    )

                deleted += 1

            except (OSError, ValueError, Http404) as error:
                errors += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"Error en trabajo #{job.pk}: {error}"
                    )
                )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Simulación terminada. Audios vencidos encontrados: "
                    f"{candidates}. Errores: {errors}."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Limpieza terminada. Eliminados: {deleted}. "
                    f"Errores: {errors}."
                )
            )
