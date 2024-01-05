import base64
import json
import logging
from http import HTTPStatus

from django.http import Http404, JsonResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from keycloak import KeycloakPostError

from .models import KeycloakProvider, KeycloakSession
from .oidc import auth_oidc
from .signals import sso_user_logout

logger = logging.getLogger('django_admin_keycloak')


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
        except KeycloakPostError as e:
            logger.error(e)
            return redirect('oidc-login-error')

        return HttpResponseRedirect(redirect_uri)


@method_decorator(csrf_exempt, name='dispatch')
class KeycloakLogoutView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = self.get_data_from_token()
            sso_session = KeycloakSession.objects.select_related('provider').get(sid=data.get('sid'))
            request.session.delete(sso_session.django_session_key)
            sso_session.delete()
            sso_user_logout.send(sso_session.__class__, session=sso_session, request=request)

        except KeycloakSession.DoesNotExist:
            logger.warning('Session does not exist')
        except Exception as e:
            logger.error(e, exc_info=True)
        return JsonResponse({}, status=HTTPStatus.OK)

    def get_data_from_token(self) -> dict:
        token = self.request.body.decode('utf-8').split('=', maxsplit=1)[1]
        base64_string = token.split('.')[1]
        return json.loads(base64.b64decode(f'{base64_string}====').decode('utf-8'))
