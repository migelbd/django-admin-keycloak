from django.apps import AppConfig
from django.conf import settings
from django.core import checks
from django.core.checks import Error


def check_options(app_configs, **kwargs):
    keycloak_config = getattr(settings, 'KEYCLOAK_CONFIG')
    errors = []
    if isinstance(keycloak_config, dict) and keycloak_config.get('enabled', False):
        options = keycloak_config.get('options', {})
        if not options.get('server_url'):
            errors.append(Error("The KEYCLOAK_CONFIG[server_url] setting must be an set", id="key_backend.E101"))
        if not options.get('client_id'):
            errors.append(Error("The KEYCLOAK_CONFIG[client_id] setting must be an set", id="key_backend.E101"))
        if not options.get('realm_name'):
            errors.append(Error("The KEYCLOAK_CONFIG[realm_name] setting must be an set", id="key_backend.E101"))
        if not options.get('client_secret_key'):
            errors.append(Error("The KEYCLOAK_CONFIG[client_secret_key] setting must be an set", id="key_backend.E101"))

    return errors


class KeyBackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django-admin-keycloak"
    verbose_name = "Keycloak"

    def ready(self):
        checks.register(check_options, 'keycloak')
