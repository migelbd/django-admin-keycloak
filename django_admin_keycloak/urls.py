from django.urls import path

from .views import KeycloakLoginView, KeycloakLogoutView, KeycloakErrorView

urlpatterns = [
    path('login/<slug:keycloak_slug>', KeycloakLoginView.as_view(), name='oidc-login'),
    path('logout', KeycloakLogoutView.as_view(), name='oidc-logout'),
    path('error', KeycloakErrorView.as_view(), name='oidc-login-error'),
]
