from django.core.management import BaseCommand

from django_admin_keycloak.models import KeycloakProvider
from django_admin_keycloak.static_settings import PROVIDERS


class Command(BaseCommand):
    help = 'Updates static Keycloak providers'

    @staticmethod
    def remove_static_providers(*slugs):
        qs = KeycloakProvider.objects.exclude(slug__in=slugs).filter(is_static=True)
        names = list(qs.values_list('name', flat=True))

        qs.delete()
        return names

    @staticmethod
    def create_or_update_provider(provider: dict) -> tuple['KeycloakProvider', bool]:
        provider.setdefault('options', {
            'verify': True,
            'custom_headers': None,
            'proxies': None,
            'timeout': 60
        })
        provider.setdefault('redirect_uri', '/')
        provider.setdefault('active', True)
        provider['is_static'] = True
        allowed_field = [f.name for f in KeycloakProvider._meta.get_fields()]
        defaults = {}
        for k, v in provider.items():
            if k in allowed_field:
                defaults[k] = v

        return KeycloakProvider.objects.update_or_create(defaults=defaults, slug=defaults['slug'])

    def handle(self, *args, **options):
        providers = PROVIDERS or []

        for provider in providers:
            obj, created = self.create_or_update_provider(provider)
            self.stdout.write(f'- {"Updating" if not created else "Created"} provider {obj}\n')

        for name in self.remove_static_providers(*[provider['slug'] for provider in providers]):
            self.stdout.write(f'- Remove provider {name}\n')
