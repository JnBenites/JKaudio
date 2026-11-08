
from django.conf import settings
from django.db import models


class GenerationJob(models.Model):

    class Status(models.TextChoices):
        QUEUED = 'queued', 'En cola'
        PROCESSING = 'processing', 'Procesando'
        COMPLETED = 'completed', 'Completado'
        FAILED = 'failed', 'Fallido'
        CANCELLED = 'cancelled', 'Cancelado'
        EXPIRED = 'expired', 'Expirado'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generation_jobs'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
        db_index=True
    )

    # Identificador protegido de la IP, no la IP original.
    ip_hash = models.CharField(
        max_length=64,
        blank=True,
        db_index=True
    )

    # Información temporal del audio.
    audio_path = models.CharField(
        max_length=500,
        blank=True
    )

    audio_duration = models.FloatField(
        null=True,
        blank=True
    )

    # Fechas del procesamiento.
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Información de descargas.
    downloaded = models.BooleanField(default=False)
    download_count = models.PositiveIntegerField(default=0)
    downloaded_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f'Generación #{self.pk} - {self.get_status_display()}'


class GenerationEvent(models.Model):

    class EventType(models.TextChoices):
        REQUESTED = 'requested', 'Solicitud recibida'
        QUEUED = 'queued', 'Agregado a cola'
        STARTED = 'started', 'Procesamiento iniciado'
        COMPLETED = 'completed', 'Generación completada'
        DOWNLOADED = 'downloaded', 'Audio descargado'
        FAILED = 'failed', 'Error de generación'
        CANCELLED = 'cancelled', 'Generación cancelada'
        EXPIRED = 'expired', 'Audio eliminado'

    job = models.ForeignKey(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name='events'
    )

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        db_index=True
    )

    detail = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.job_id} - {self.get_event_type_display()}'
