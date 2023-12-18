from django.urls import path

from .views import auth_callback

urlpatterns = [
    path('callback/<slug:keycloak_slug>', auth_callback, name='oidc-login')
]
