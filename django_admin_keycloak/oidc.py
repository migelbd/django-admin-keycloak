import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model, login
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from keycloak import KeycloakOpenID

from django_admin_keycloak.models import KeycloakProvider, KeycloakUser
from django_admin_keycloak.signals import sso_user_login
from django_admin_keycloak.utils import save_sso_session

UserModel = get_user_model()

STATE_SESSION_KEY = 'keycloak_oidc_states'
MAX_PENDING_STATES = 10


class KeycloakLoginError(Exception):
    """Raised when the OIDC login flow must be rejected (bad state, account conflict)."""


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


def get_auth_url(provider: KeycloakProvider, request: HttpRequest) -> str:
    oidc_client = get_oidc_client(provider)
    next_url = get_next_url(request, provider.redirect_uri)
    state = _store_state(request, next_url)
    return oidc_client.auth_url(
        request.build_absolute_uri(reverse('oidc-login', kwargs={'keycloak_slug': provider.slug})),
        scope=provider.scope,
        state=state
    )


def _store_state(request: HttpRequest, next_url: str) -> str:
    """Generate a random state nonce and remember the redirect target for it in the session."""
    state = secrets.token_urlsafe(32)
    states = request.session.get(STATE_SESSION_KEY) or {}
    # Bound the number of pending states to avoid unbounded session growth.
    if len(states) >= MAX_PENDING_STATES:
        states = {}
    states[state] = next_url
    request.session[STATE_SESSION_KEY] = states
    request.session.modified = True
    return state


def _pop_state(request: HttpRequest, state: str | None) -> str | None:
    """Return (and consume) the redirect target stored for ``state``; None if unknown."""
    if not state:
        return None
    states = request.session.get(STATE_SESSION_KEY)
    if not states or state not in states:
        return None
    next_url = states.pop(state)
    request.session[STATE_SESSION_KEY] = states
    request.session.modified = True
    return next_url


def get_next_url(request: HttpRequest, default: str) -> str:
    try:
        next_url = request.GET['next']
        if isinstance(next_url, (list, tuple)):
            next_url = next_url[0]
        return next_url
    except KeyError:
        return default


def _safe_redirect_url(request: HttpRequest, url: str | None, default: str) -> str:
    """Only allow same-host redirects; fall back to the provider default otherwise."""
    if url and url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return url
    return default


def auth_oidc(provider: KeycloakProvider, request: HttpRequest):
    oidc_client = get_oidc_client(provider)
    code = request.GET.get('code')
    if not code:
        raise KeycloakLoginError('Missing authorization code')

    # Validate the OIDC state nonce against the value we stored before the redirect.
    # This is the CSRF protection for the callback and also carries the redirect target.
    next_url = _pop_state(request, request.GET.get('state'))
    if next_url is None:
        raise KeycloakLoginError('Invalid or missing OIDC state')

    sid = request.GET.get('session_state')
    access_token = oidc_client.token(
        grant_type='authorization_code',
        code=code,
        redirect_uri=request.build_absolute_uri(reverse('oidc-login', kwargs={'keycloak_slug': provider.slug}))
    )

    userinfo = oidc_client.userinfo(token=access_token['access_token'])
    user = create_user(provider, userinfo)

    login(request, user)

    sso_session = save_sso_session(request, provider, sid)

    check_permissions(provider, user, userinfo)
    check_member_of(provider, user, userinfo)

    if sso_session is not None:
        sso_user_login.send(
            sso_session.__class__,
            session=sso_session,
            request=request,
            userinfo=userinfo,
            access_token=access_token
        )

    refresh_expiry = access_token.get('refresh_expires_in') or access_token.get('expires_in')
    if refresh_expiry and refresh_expiry > 0:
        request.session.set_expiry(timedelta(seconds=refresh_expiry))

    return _safe_redirect_url(request, next_url, provider.redirect_uri)


def create_user(provider: KeycloakProvider, userinfo: dict) -> UserModel:
    username = userinfo['preferred_username']

    # Prefer an already-linked SSO account for this provider. This avoids matching a
    # Keycloak identity onto an unrelated local account that merely shares a username.
    keycloak_user = (
        KeycloakUser.objects
        .filter(provider=provider, preferred_username=username)
        .select_related('user')
        .first()
    )
    if keycloak_user:
        return keycloak_user.user

    try:
        user = UserModel._default_manager.get_by_natural_key(username)
    except UserModel.DoesNotExist:
        return UserModel.objects.create_user(
            username=username,
            email=userinfo.get('email'),
            first_name=userinfo.get('given_name', ''),
            last_name=userinfo.get('family_name', '')
        )

    # A local account with this username exists but is not linked to this provider's
    # KeycloakUser. Refuse rather than silently adopting it (prevents account takeover).
    raise KeycloakLoginError(
        f'Username {username!r} already belongs to a non-SSO account'
    )


def check_permissions(provider: KeycloakProvider, user: UserModel, userinfo: dict):
    groups = userinfo.get('groups')
    # ``None`` means the provider does not emit a groups claim, so we do not manage
    # these flags. An empty list means "no roles" and must revoke stale privileges.
    if groups is None:
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
    if groups is None:
        return
    # Keycloak is the source of truth for group membership when the claim is present.
    user.groups.clear()
    user.groups.add(*Group.objects.filter(name__in=groups))
