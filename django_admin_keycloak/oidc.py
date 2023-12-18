from functools import lru_cache

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import HttpRequest
from django.urls import reverse
from keycloak import KeycloakOpenID

UserModel = get_user_model()


@lru_cache
def get_oidc_client() -> KeycloakOpenID:
    options = settings.KEYCLOAK_CONFIG['options']
    return KeycloakOpenID(**options)


def get_auth_url(request: HttpRequest, state: str | None = None) -> str:
    return get_oidc_client().auth_url(
        request.build_absolute_uri(reverse('oidc-login')),
        scope='openid profile email',
        state=state or ''
    )


def auth_oidc(request: HttpRequest, code: str, redirect_uri: str):
    oidc_client = get_oidc_client()
    access_token = oidc_client.token(
        grant_type='authorization_code',
        code=code,
        redirect_uri=request.build_absolute_uri(reverse('oidc-login'))
    )
    request.session['keycloak_access_token'] = access_token

    userinfo = oidc_client.userinfo(token=access_token['access_token'])

    user = create_user(userinfo)
    check_permissions(user, userinfo)
    login(request, user)
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


def check_permissions(user: UserModel, userinfo: dict):
    groups = userinfo['groups']
    superuser_role = settings.KEYCLOAK_CONFIG.get('superuser_role')
    staff_role = settings.KEYCLOAK_CONFIG.get('staff_role')
    is_superuser = superuser_role in groups
    is_staff = staff_role in groups
    changed = False
    if user.is_superuser != is_superuser:
        user.is_superuser = is_superuser
        changed = True
    if user.is_staff != is_staff:
        user.is_staff = is_staff
        changed = True
    if changed:
        user.save(update_fields=['is_superuser', 'is_staff'])
