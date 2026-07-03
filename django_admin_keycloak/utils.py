import logging
from datetime import timedelta

from django.utils import timezone

from .models import KeycloakSession, KeycloakProvider

logger = logging.getLogger('django_admin_keycloak')


def save_sso_session(request, provider: KeycloakProvider, keycloak_session: str | None):
    request.session['keycloak_pk'] = provider.pk

    # ``keycloak_session`` (the ``session_state`` param) is the primary key of
    # KeycloakSession. Without it we cannot track the SSO session for back-channel
    # logout, so skip creating a row rather than crashing on a NULL UUID PK.
    if not keycloak_session:
        logger.warning('No session_state returned by Keycloak; skipping SSO session tracking')
        clear_sso_session()
        return None

    try:
        session = KeycloakSession.objects.get(pk=keycloak_session)
        session.django_session_key = request.session.session_key
        session.save(update_fields=['django_session_key'])
    except KeycloakSession.DoesNotExist:
        session = KeycloakSession.objects.create(
            provider=provider,
            sid=keycloak_session,
            django_session_key=request.session.session_key,
            user=request.user
        )
    clear_sso_session()
    return session


def clear_sso_session():
    KeycloakSession.objects.filter(created_at__lt=timezone.now() - timedelta(days=30)).delete()
