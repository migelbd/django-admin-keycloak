from .models import KeycloakSession, KeycloakProvider


def save_sso_session(request, provider: KeycloakProvider, keycloak_session: str):
    return KeycloakSession.objects.create(
        provider=provider,
        sid=keycloak_session,
        django_session_key=request.session.session_key,
        user=request.user,
    )
