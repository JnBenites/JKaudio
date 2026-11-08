
from django.urls import path
from . import views

app_name = 'generator'

urlpatterns = [
    path(
        'validar/',
        views.validate_generation,
        name='validate_generation'
    ),

    path(
        'estado/<int:job_id>/',
        views.job_status,
        name='job_status'
    ),

    path(
        'descargar/<int:job_id>/',
        views.download_audio,
        name='download_audio'
    ),
    path(
    'reproducir/<int:job_id>/',
    views.stream_audio,
    name='stream_audio'
),
]
