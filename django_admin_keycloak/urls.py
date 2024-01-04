from django.urls import path

from .views import auth_callback, auth_logout

urlpatterns = [
    path('callback/<slug:keycloak_slug>', auth_callback, name='oidc-login'),
    path('sso-logout', auth_logout, name='oidc-logout'),
    path('sso-error', auth_logout, name='oidc-login-error'),
]
