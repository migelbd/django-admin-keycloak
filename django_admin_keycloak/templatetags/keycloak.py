from django import template
from django.conf import settings
from django_admin_keycloak.oidc import get_auth_url

register = template.Library()


@register.simple_tag(takes_context=True)
def keycloak_authorization_url(context):
    request = context['request']
    return get_auth_url(request)


@register.inclusion_tag('django_admin_keycloak/auth_link.html', takes_context=True)
def keycloak_authorization_link(context):
    request = context['request']
    name = settings.KEYCLOAK_CONFIG.get('name', 'OpenID Connect')
    return {
        'url': get_auth_url(request),
        'name': f'Войти через {name}'
    }


@register.simple_tag()
def keycloak_enabled():
    return settings.KEYCLOAK_CONFIG.get('enabled', False)
