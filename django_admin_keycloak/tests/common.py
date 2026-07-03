"""Shared helpers for the test suite (not collected as tests itself)."""
from django.contrib.auth import get_user_model

from django_admin_keycloak.models import KeycloakProvider

User = get_user_model()


class DummySession(dict):
    """Minimal stand-in for request.session (dict + a settable ``modified`` flag)."""
    modified = False


def make_provider(**overrides):
    defaults = dict(
        slug='devconf',
        name='DevConf',
        server_url='https://id.example',
        realm_name='devconf',
        client_id='local_django',
        client_secret='secret',
        role_super_user='django-superuser',
        role_staff_user='django-staff',
    )
    defaults.update(overrides)
    return KeycloakProvider.objects.create(**defaults)
