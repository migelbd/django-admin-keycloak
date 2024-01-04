from django.apps import AppConfig
from django.core.checks import register


class DjangoAdminKeycloakConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_admin_keycloak"
    verbose_name = "Keycloak"

    def ready(self):
        from django_admin_keycloak.static_settings import check_static_config
        register(check_static_config, 'keycloak', name="keycloak_static_config")
