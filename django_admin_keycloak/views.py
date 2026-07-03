import base64
import json
import logging
import urllib.parse
from http import HTTPStatus

from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from .models import KeycloakProvider, KeycloakSession
from .oidc import KeycloakLoginError, auth_oidc, get_oidc_client
from .signals import sso_user_logout

logger = logging.getLogger('django_admin_keycloak')

BACKCHANNEL_LOGOUT_EVENT = 'http://schemas.openid.net/event/backchannel-logout'


class KeycloakErrorView(TemplateView):
    template_name = 'django_admin_keycloak/login-error.html'


class KeycloakLoginView(View):
    def get(self, request, keycloak_slug: str):
        try:
            provider = KeycloakProvider.objects.get(slug=keycloak_slug)
        except KeycloakProvider.DoesNotExist:
            raise Http404("Not Found")
        try:
            redirect_uri = auth_oidc(
                provider=provider,
                request=request
            )
        except KeycloakLoginError as e:
            logger.warning('Keycloak login rejected: %s', e)
            return redirect('oidc-login-error')
        except Exception as e:
            logger.error(e, exc_info=True)
            return redirect('oidc-login-error')

        return HttpResponseRedirect(redirect_uri)


@method_decorator(csrf_exempt, name='dispatch')
class KeycloakLogoutView(View):
    def post(self, request, *args, **kwargs):
        logout_token = self.get_logout_token(request)
        if not logout_token:
            return JsonResponse({'error': 'invalid_request'}, status=HTTPStatus.BAD_REQUEST)

        try:
            claims = self.decode_unverified(logout_token)
        except Exception:
            logger.warning('Malformed logout token')
            return JsonResponse({'error': 'invalid_request'}, status=HTTPStatus.BAD_REQUEST)

        sid = claims.get('sid')
        if not sid:
            return JsonResponse({'error': 'invalid_request'}, status=HTTPStatus.BAD_REQUEST)

        try:
            sso_session = KeycloakSession.objects.select_related('provider').get(sid=sid)
        except (ValueError, ValidationError):
            return JsonResponse({'error': 'invalid_request'}, status=HTTPStatus.BAD_REQUEST)
        except KeycloakSession.DoesNotExist:
            # Idempotent: nothing to log out. Do not leak whether the sid existed.
            logger.warning('Session does not exist')
            return JsonResponse({}, status=HTTPStatus.OK)

        # Verify the logout token signature with the realm public key before acting on it.
        oidc_client = get_oidc_client(sso_session.provider)
        try:
            verified = oidc_client.decode_token(logout_token, validate=True)
        except Exception as e:
            logger.warning('Logout token validation failed: %s', e)
            return JsonResponse({'error': 'invalid_token'}, status=HTTPStatus.BAD_REQUEST)

        if verified.get('sid') != str(sso_session.sid):
            return JsonResponse({'error': 'invalid_token'}, status=HTTPStatus.BAD_REQUEST)
        events = verified.get('events') or {}
        if BACKCHANNEL_LOGOUT_EVENT not in events:
            return JsonResponse({'error': 'invalid_token'}, status=HTTPStatus.BAD_REQUEST)

        try:
            request.session.delete(sso_session.django_session_key)
            sso_session.delete()
            sso_user_logout.send(sso_session.__class__, session=sso_session, request=request)
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'error': 'server_error'}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        return JsonResponse({}, status=HTTPStatus.OK)

    @staticmethod
    def get_logout_token(request) -> str | None:
        body = request.body.decode('utf-8', errors='replace')
        tokens = urllib.parse.parse_qs(body).get('logout_token')
        return tokens[0] if tokens else None

    @staticmethod
    def decode_unverified(token: str) -> dict:
        """Decode the JWT payload without signature validation (to locate the session)."""
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload).decode('utf-8'))
