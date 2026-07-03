"""admin #8 — get_exclude returns a list (never None) for static providers."""
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from django_admin_keycloak.admin import KeycloakProviderAdmin
from django_admin_keycloak.models import KeycloakProvider

from .common import make_provider


class AdminGetExcludeTests(TestCase):
    def setUp(self):
        self.admin = KeycloakProviderAdmin(KeycloakProvider, AdminSite())
        self.request = RequestFactory().get('/admin/')

    def test_static_provider_excludes_client_secret_as_list(self):
        provider = make_provider(is_static=True)
        excluded = self.admin.get_exclude(self.request, provider)
        self.assertIsInstance(excluded, list)
        self.assertIn('client_secret', excluded)

    def test_dynamic_provider_returns_list_without_secret(self):
        provider = make_provider(slug='dyn', is_static=False)
        excluded = self.admin.get_exclude(self.request, provider)
        self.assertIsInstance(excluded, list)
        self.assertNotIn('client_secret', excluded)
