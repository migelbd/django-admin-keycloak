from django.conf import settings
from django.http import HttpResponseRedirect

from .oidc import auth_oidc


def auth_callback(request):
    redirect_uri = auth_oidc(
        request,
        code=request.GET.get('code'),
        redirect_uri=settings.KEYCLOAK_CONFIG.get('redirect_url', '/')
    )

    return HttpResponseRedirect(redirect_uri)
