from .models import KeycloakSession, KeycloakProvider


def save_sso_session(request, provider: KeycloakProvider, keycloak_session: str, keycloak_access_token: dict):
    request.session['keycloak_sid'] = keycloak_session
    request.session['keycloak_access_token'] = keycloak_access_token
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
    return session
