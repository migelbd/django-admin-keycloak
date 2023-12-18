from django import template
from django_admin_keycloak.models import KeycloakProvider
from django_admin_keycloak.oidc import get_auth_url

register = template.Library()


@register.simple_tag(takes_context=True)
def keycloak_authorization_url(context):
    request = context['request']
    return get_auth_url(request)


def _get_providers(request):
    for provider in KeycloakProvider.objects.filter(active=True).iterator():
        yield {
            'name': provider.name,
            'url': get_auth_url(provider, request)
        }


@register.inclusion_tag('django_admin_keycloak/auth_link.html', takes_context=True)
def keycloak_authorization_links(context):
    request = context['request']
    count = KeycloakProvider.objects.filter(active=True).count()
    return {
        'providers': _get_providers(request),
        'has_one': count == 1,
        'has_many': count > 1
    }
