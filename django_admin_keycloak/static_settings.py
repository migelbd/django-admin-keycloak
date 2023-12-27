from django.conf import settings
from django.core.checks import Error

PROVIDERS = getattr(settings, 'KEYCLOAK_PROVIDERS', None)

REQUIRED_PROPERTIES = (
    'slug',
    'name',
    'server_url',
    'realm_name',
    'client_id',
    'client_secret',
    'redirect_uri',
    'role_super_user',
    'role_staff_user',
)


def check_static_config(app_configs, **kwargs):
    errors = []
    if PROVIDERS is None:
        return errors

    for provider in PROVIDERS:
        for rq in REQUIRED_PROPERTIES:
            if (rq in provider and provider[rq] is None) or rq not in provider:
                errors.append(Error(f'Missing required property {rq}'))
    return errors
