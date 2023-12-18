from django.urls import path

from .views import auth_callback

urlpatterns = [
    path('callback', auth_callback, name='oidc-login')
]
