from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'accounts'

urlpatterns = [
    path(
        'registro/',
        views.register,
        name='register'
    ),

    path(
        'entrar/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html'
        ),
        name='login'
    ),

    path(
        'salir/',
        auth_views.LogoutView.as_view(
            next_page='home'
        ),
        name='logout'
    ),
]