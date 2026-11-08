
from django.contrib import admin
from .models import ServiceSettings


@admin.register(ServiceSettings)
class ServiceSettingsAdmin(admin.ModelAdmin):

    list_display = (
        'max_generations_per_ip_per_day',
        'max_text_length',
        'audio_retention_minutes',
        'generation_enabled',
        'maintenance_mode',
        'updated_at',
    )

    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        return not ServiceSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
