import logging

from django.http import Http404
from django.http import HttpResponseRedirect
from keycloak import KeycloakPostError

from .models import KeycloakProvider
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
            request=request,
            code=request.GET.get('code'),
            redirect_uri=provider.redirect_uri
        )
    except KeycloakPostError as e:
        logger.error(e)
        return HttpResponseRedirect('/')

    return HttpResponseRedirect(redirect_uri)
