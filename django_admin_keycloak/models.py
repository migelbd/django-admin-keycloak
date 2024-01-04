from django.contrib.auth import get_user_model
from django.contrib.sessions.base_session import AbstractBaseSession

from django.db import models
from django.db.models.signals import post_delete
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
    client_secret = models.CharField(_('client secret key'), max_length=128, blank=True, null=True)
    scope = models.TextField(_('scope'), default='openid profile')

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
    is_static = models.BooleanField(_('is static'), default=False, editable=False)

    def __str__(self):
        return self.name or self.realm_name

    def get_account_link(self) -> str:
        return f'{self.server_url}/realms/{self.realm_name}/account'

    class Meta:
        db_table = 'keycloak_provider'
        verbose_name = _('Keycloak Provider')
        verbose_name_plural = _('Keycloak Provider')


class KeycloakSession(models.Model):
    provider = models.ForeignKey(KeycloakProvider, on_delete=models.CASCADE, related_name='sessions')
    sid = models.UUIDField(primary_key=True, verbose_name=_('SID'), editable=False)
    django_session_key = models.CharField(_("session key"), max_length=40)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='sso_sessions')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    def __str__(self):
        return str(self.sid)

    class Meta:
        db_table = "keycloak_session"
        verbose_name = _('Keycloak Session')
        verbose_name_plural = _('Keycloak Sessions')


def delete_session(sender, instance: KeycloakSession, **kwargs):
    try:
        from django.contrib.sessions.models import Session
        Session.objects.filter(pk=instance.django_session_key).delete()
    except Exception:
        pass


post_delete.connect(delete_session, sender=KeycloakSession)
