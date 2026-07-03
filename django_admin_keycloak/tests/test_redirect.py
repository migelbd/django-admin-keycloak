"""#3 — open redirect: only same-host targets are honoured."""
from django.test import RequestFactory, SimpleTestCase

from django_admin_keycloak import oidc


class SafeRedirectTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')  # host == 'testserver', is_secure() False

    def test_external_url_falls_back_to_default(self):
        self.assertEqual(
            oidc._safe_redirect_url(self.request, 'https://evil.com/steal', '/admin'),
            '/admin',
        )

    def test_protocol_relative_url_falls_back(self):
        self.assertEqual(
            oidc._safe_redirect_url(self.request, '//evil.com', '/admin'),
            '/admin',
        )

    def test_none_falls_back(self):
        self.assertEqual(oidc._safe_redirect_url(self.request, None, '/admin'), '/admin')

    def test_relative_path_is_allowed(self):
        self.assertEqual(
            oidc._safe_redirect_url(self.request, '/admin/dashboard', '/admin'),
            '/admin/dashboard',
        )

    def test_same_host_absolute_is_allowed(self):
        self.assertEqual(
            oidc._safe_redirect_url(self.request, 'http://testserver/admin', '/admin'),
            'http://testserver/admin',
        )
