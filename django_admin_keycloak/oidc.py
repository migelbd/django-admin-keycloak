from datetime import timedelta

from django.contrib.auth import get_user_model, login
from django.contrib.auth.models import Group, User
from django.http import HttpRequest
from django.urls import reverse
from keycloak import KeycloakOpenID

from django_admin_keycloak.models import KeycloakProvider
from django_admin_keycloak.signals import sso_user_login
from django_admin_keycloak.utils import save_sso_session

UserModel = get_user_model()


def get_oidc_client_by_pk(pk: int) -> KeycloakOpenID | None:
    try:
        provider = KeycloakProvider.objects.get(pk=pk)
    except KeycloakProvider.DoesNotExist:
        return
    return get_oidc_client(provider)


def get_oidc_client_by_slug(slug: str) -> KeycloakOpenID | None:
    try:
        provider = KeycloakProvider.objects.get(slug=slug)
    except KeycloakProvider.DoesNotExist:
        return
    return get_oidc_client(provider)


def get_oidc_client(provider: KeycloakProvider) -> KeycloakOpenID:
    return KeycloakOpenID(
        server_url=provider.server_url,
        realm_name=provider.realm_name,
        client_id=provider.client_id,
        client_secret_key=provider.client_secret,
        **provider.options
    )


def get_auth_url(provider: KeycloakProvider, request: HttpRequest, state: str | None = None) -> str:
    oidc_client = get_oidc_client(provider)
    return oidc_client.auth_url(
        request.build_absolute_uri(reverse('oidc-login', kwargs={'keycloak_slug': provider.slug})),
        scope=provider.scope,
        state=state or get_next_url(request, '')
    )


def get_next_url(request: HttpRequest, default: str) -> str:
    try:
        next_url = request.GET['next']
        if isinstance(next_url, (list, tuple)):
            next_url = next_url[0]
        return next_url
    except KeyError:
        return default


def get_url_from_state(request: HttpRequest, default: str) -> str:
    try:
        next_url = request.GET['state']
        if isinstance(next_url, (list, tuple)):
            next_url = next_url[0]
        return next_url
    except KeyError:
        return default


def auth_oidc(provider: KeycloakProvider, request: HttpRequest):
    oidc_client = get_oidc_client(provider)
    code = request.GET.get('code')
    sid = request.GET.get('session_state')
    access_token = oidc_client.token(
        grant_type='authorization_code',
        code=code,
        redirect_uri=request.build_absolute_uri(reverse('oidc-login', kwargs={'keycloak_slug': provider.slug}))
    )

    userinfo = oidc_client.userinfo(token=access_token['access_token'])
    user = create_user(userinfo)

    login(request, user)

    sso_session = save_sso_session(request, provider, sid, access_token)

    check_permissions(provider, user, userinfo)
    check_member_of(provider, user, userinfo)

    sso_user_login.send(
        sso_session.__class__,
        session=sso_session,
        request=request,
        userinfo=userinfo,
        access_token=access_token
    )

    request.session.set_expiry(timedelta(seconds=access_token['refresh_expires_in']))

    return get_url_from_state(request, provider.redirect_uri)


def create_user(userinfo: dict) -> UserModel:
    username = userinfo['preferred_username']
    try:
        user = UserModel._default_manager.get_by_natural_key(username)
    except UserModel.DoesNotExist:
        user = UserModel.objects.create_user(
            username=username,
            email=userinfo['email'],
            first_name=userinfo['given_name'],
            last_name=userinfo['family_name']
        )
    return user


def check_permissions(provider: KeycloakProvider, user: UserModel, userinfo: dict):
    groups = userinfo.get('groups')
    if not groups:
        return

    is_superuser = provider.role_super_user in groups
    is_staff = provider.role_staff_user in groups
    changed = False
    if user.is_superuser != is_superuser:
        user.is_superuser = is_superuser
        changed = True
    if user.is_staff != is_staff:
        user.is_staff = is_staff
        changed = True
    if changed:
        user.save(update_fields=['is_superuser', 'is_staff'])


def check_member_of(provider: KeycloakProvider, user: UserModel, userinfo: dict):
    groups = userinfo.get('groups')
    if not groups:
        return
    user.groups.clear()
    user.groups.add(*Group.objects.filter(name__in=groups))
