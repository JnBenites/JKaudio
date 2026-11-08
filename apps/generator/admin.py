
from django.contrib import admin
from .models import GenerationJob, GenerationEvent


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'status',
        'created_at',
        'audio_duration',
        'download_count',
    )

    list_filter = ('status', 'created_at')

    search_fields = ('user__username',)

    readonly_fields = (
        'created_at',
        'started_at',
        'finished_at',
        'downloaded_at',
    )


@admin.register(GenerationEvent)
class GenerationEventAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'job',
        'event_type',
        'created_at',
    )

    list_filter = ('event_type', 'created_at')

    readonly_fields = (
        'job',
        'event_type',
        'detail',
        'created_at',
    )
