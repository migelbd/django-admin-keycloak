from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

UserModel = get_user_model()


def _default_options() -> dict:
    return {
        'verify': True,
        'custom_headers': None,
        'proxies': None,
        'timeout': 60
    }


class KeycloakProvider(models.Model):
    active = models.BooleanField(_('active'), default=True)
    slug = models.SlugField(_('slug'), unique=True)
    name = models.CharField(_('name'), max_length=128)

    server_url = models.URLField(_('server url'))
    realm_name = models.CharField(_('realm name'), max_length=128)
    client_id = models.CharField(_('client id'), max_length=128)
    client_secret_key = models.CharField(_('client secret key'), max_length=128, blank=True, null=True)

    redirect_uri = models.CharField(
        _('redirect_uri'),
        max_length=256,
        default='/',
        help_text=_('The redirect URI for user is not staff')
    )
    role_super_user = models.CharField(_('superuser role'), max_length=128, default='superuser')
    role_staff_user = models.CharField(_('staff user role'), max_length=128, default='staff')

    options = models.JSONField(
        _('options'),
        default=_default_options,
        help_text=_('Available options list see https://python-keycloak.readthedocs.io/')
    )

    class Meta:
        db_table = 'keycloak_provider'
        verbose_name = _('Keycloak Provider')
        verbose_name_plural = _('Keycloak Provider')
