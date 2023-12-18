from datetime import timedelta

from django.contrib.auth import get_user_model, login
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from keycloak import KeycloakOpenID

from django_admin_keycloak.models import KeycloakProvider

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
        client_secret_key=provider.client_secret_key,
        **provider.options
    )


def get_auth_url(provider: KeycloakProvider, request: HttpRequest, state: str | None = None) -> str:
    oidc_client = get_oidc_client(provider)
    return oidc_client.auth_url(
        request.build_absolute_uri(reverse('oidc-login', kwargs={'keycloak_slug': provider.slug})),
        scope='openid profile',
        state=state or ''
    )


def auth_oidc(provider: KeycloakProvider, request: HttpRequest, code: str, redirect_uri: str):
    oidc_client = get_oidc_client(provider)
    access_token = oidc_client.token(
        grant_type='authorization_code',
        code=code,
        redirect_uri=request.build_absolute_uri(reverse('oidc-login', kwargs={'keycloak_slug': provider.slug}))
    )

    request.session['keycloak'] = {
        'token': access_token,
        'pk': provider.pk
    }

    userinfo = oidc_client.userinfo(token=access_token['access_token'])

    user = create_user(userinfo)
    check_permissions(provider, user, userinfo)
    login(request, user)
    request.session.set_expiry(timedelta(seconds=access_token['refresh_expires_in']))
    if user.is_staff:
        return reverse('admin:index')
    else:
        return redirect_uri


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
    groups = userinfo['groups']

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
