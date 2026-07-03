"""#14 / #15 — static config check and the update_static_providers command."""
from unittest import mock

from django.core.checks import Error
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from django_admin_keycloak import static_settings
from django_admin_keycloak.models import KeycloakProvider


class StaticConfigCheckTests(SimpleTestCase):
    """#15 — client_secret is optional (public clients)."""

    def test_client_secret_not_required(self):
        self.assertNotIn('client_secret', static_settings.REQUIRED_PROPERTIES)

    def test_public_client_without_secret_passes(self):
        provider = {
            'slug': 's', 'name': 'n', 'server_url': 'https://x', 'realm_name': 'r',
            'client_id': 'c', 'redirect_uri': '/', 'role_super_user': 'a',
            'role_staff_user': 'b',
        }
        with mock.patch.object(static_settings, 'PROVIDERS', [provider]):
            self.assertEqual(static_settings.check_static_config(None), [])

    def test_missing_required_property_reports_error(self):
        provider = {'name': 'n'}  # missing slug etc.
        with mock.patch.object(static_settings, 'PROVIDERS', [provider]):
            errors = static_settings.check_static_config(None)
        self.assertTrue(errors)
        self.assertIsInstance(errors[0], Error)


class UpdateStaticProvidersCommandTests(TestCase):
    """#14 — a provider without a slug is skipped, not a crash."""

    def test_provider_without_slug_is_skipped(self):
        providers = [
            {'slug': 'ok', 'name': 'OK', 'server_url': 'https://x', 'realm_name': 'r',
             'client_id': 'c'},
            {'name': 'no-slug'},  # must be skipped, not crash
        ]
        target = 'django_admin_keycloak.management.commands.update_static_providers.PROVIDERS'
        with mock.patch(target, providers):
            call_command('update_static_providers')
        self.assertTrue(KeycloakProvider.objects.filter(slug='ok', is_static=True).exists())
        self.assertEqual(KeycloakProvider.objects.count(), 1)
