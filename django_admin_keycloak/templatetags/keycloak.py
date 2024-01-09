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
    return {
        'providers': _get_providers(request),
    }


@register.simple_tag(name='sso_account', takes_context=True)
def get_account_link(context):
    request = context['request']
    try:
        provider = KeycloakProvider.objects.get(pk=request.session['keycloak_pk'])
    except (KeycloakProvider.DoesNotExist, KeyError):
        return

    return provider.get_account_link()
