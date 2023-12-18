import zoneinfo
from datetime import datetime

from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from .oidc import get_oidc_client


class KeyBackendMiddleware(MiddlewareMixin):
    async_capable = False

    def process_request(self, request):
        if request.session.has_key('keycloak_access_token'):
            keycloak_openid = get_oidc_client()
            access_token = request.session.get('keycloak_access_token')
            token_info = keycloak_openid.introspect(access_token['access_token'])
            if not token_info.get('active', True):
                del request.session['keycloak_access_token']
                logout(request)
                return self.get_response(request)
            token_expiration = datetime.fromtimestamp(token_info['exp'], zoneinfo.ZoneInfo(settings.TIME_ZONE))
            if token_expiration > timezone.now():
                request.session['keycloak_access_token'] = keycloak_openid.refresh_token(access_token['refresh_token'])

        return self.get_response(request)
