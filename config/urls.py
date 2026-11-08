from django.contrib import admin
from django.urls import path, include
from apps.generator import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),

    # Accounts
    path('cuenta/', include('apps.accounts.urls')),

    # Generator
    path('generador/', include('apps.generator.urls')),

    # Operations
    path('operaciones/', include('apps.operations.urls')),
]