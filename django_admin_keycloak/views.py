import base64
import json
import logging

from django.db.transaction import atomic
from django.http import Http404, JsonResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from keycloak import KeycloakPostError

from .models import KeycloakProvider, KeycloakSession
from .oidc import auth_oidc

logger = logging.getLogger('django_admin_keycloak')


def auth_callback(request, keycloak_slug: str):
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
        return redirect('django_admin_keycloak:oidc-login-error')

    return HttpResponseRedirect(redirect_uri)


def auth_error(request):
    return render(request, 'django_admin_keycloak/login-error.html')


@csrf_exempt
def auth_logout(request):
    if not hasattr(request.session, 'sid'):
        return JsonResponse({'success': True})
    token = request.body.decode('utf-8').split('=', maxsplit=1)[1]
    base64_string = token.split('.')[1]
    data = json.loads(base64.b64decode(f'{base64_string}====').decode('utf-8'))
    sid = data.get('sid')
    with atomic():
        KeycloakSession.objects.filter(sid=sid).delete()

    return JsonResponse({'success': True})
