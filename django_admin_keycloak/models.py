from django.contrib.auth import get_user_model
from django.contrib.sessions.base_session import AbstractBaseSession
from django.contrib.sessions.models import Session

from django.db import models
from django.db.models.signals import post_delete
from django.utils.translation import gettext_lazy as _

from django_admin_keycloak.signals import sso_user_login

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
    app_name = models.CharField(_('app name'), max_length=128, blank=True)
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

    def get_account_link(self, referrer: str | None = None, referrer_uri: str | None = None) -> str:
        params = ''
        if referrer_uri:
            if not referrer:
                referrer = 'App'
            params = f'?referrer={referrer}&referrer_uri={referrer_uri}'
        return f'{self.server_url}/realms/{self.realm_name}/account{params}'

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


class KeycloakUser(models.Model):
    provider = models.ForeignKey(KeycloakProvider, on_delete=models.CASCADE, related_name='users')
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name='keycloak_user')
    preferred_username = models.CharField(_('username'), max_length=128)
    given_name = models.CharField(_('first name'), max_length=128, blank=True)
    family_name = models.CharField(_('first name'), max_length=128, blank=True)
    email = models.EmailField(_('email address'), null=True, blank=True)
    email_verified = models.BooleanField(_('email verified'), default=False)
    raw_data = models.JSONField()

    class Meta:
        db_table = "keycloak_user"
        verbose_name = _('Keycloak User')
        verbose_name_plural = _('Keycloak Users')

    def __str__(self):
        return self.preferred_username


def delete_session(sender, instance: KeycloakSession, **kwargs):
    from django.contrib.sessions.models import Session
    Session.objects.filter(pk=instance.django_session_key).delete()


def delete_keycloak_session(sender, instance: Session, **kwargs):
    KeycloakSession.objects.filter(django_session_key=instance.pk).delete()


def create_keycloak_user(sender, session: KeycloakSession, request, userinfo, **kwargs):
    fields = [f.name for f in KeycloakUser._meta.get_fields()]
    attributes = {k: v for k, v in userinfo.items() if k in fields}
    attributes['raw_data'] = userinfo
    attributes['provider'] = session.provider
    KeycloakUser.objects.update_or_create(
        defaults=attributes,
        user=request.user
    )


post_delete.connect(delete_session, sender=KeycloakSession)
post_delete.connect(delete_keycloak_session, sender=Session)
sso_user_login.connect(create_keycloak_user)
