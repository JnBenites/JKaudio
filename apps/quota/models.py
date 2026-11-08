
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class ServiceSettings(models.Model):

    max_generations_per_ip_per_day = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        verbose_name='Generaciones máximas por IP al día'
    )

    max_text_length = models.PositiveIntegerField(
        default=3000,
        validators=[MinValueValidator(1)],
        verbose_name='Máximo de caracteres'
    )

    audio_retention_minutes = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(1)],
        verbose_name='Retención del audio en minutos'
    )

    generation_enabled = models.BooleanField(
        default=True,
        verbose_name='Generación habilitada'
    )

    maintenance_mode = models.BooleanField(
        default=False,
        verbose_name='Modo mantenimiento'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    @classmethod
    def get_solo(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('La configuración principal no se puede eliminar.')

    class Meta:
        verbose_name = 'Configuración del servicio'
        verbose_name_plural = 'Configuración del servicio'

    def __str__(self):
        return 'Configuración general de JKaudio'
