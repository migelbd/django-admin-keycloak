"""#1 / #5 / #13 — logout token parsing (base64url) and status-code handling."""
import base64
import json

from django.test import RequestFactory, SimpleTestCase, TestCase

from django_admin_keycloak.views import KeycloakLogoutView


class LogoutTokenParsingTests(SimpleTestCase):
    def test_decode_unverified_handles_base64url_and_padding(self):
        payload = {'sid': 'abc-123_def', 'events': {'x': {}}, 'v': '<<??>>-_'}
        b64url = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        # ensure the payload actually exercises url-safe chars ('-' / '_')
        self.assertTrue('-' in b64url or '_' in b64url)
        token = f'header.{b64url}.signature'
        self.assertEqual(KeycloakLogoutView.decode_unverified(token), payload)

    def test_get_logout_token_parses_form_body(self):
        request = RequestFactory().post(
            '/sso/logout',
            data='logout_token=header.payload.sig',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(KeycloakLogoutView.get_logout_token(request), 'header.payload.sig')

    def test_get_logout_token_missing_returns_none(self):
        request = RequestFactory().post(
            '/sso/logout', data='', content_type='application/x-www-form-urlencoded')
        self.assertIsNone(KeycloakLogoutView.get_logout_token(request))


class LogoutViewTests(TestCase):
    def test_missing_token_returns_400(self):
        response = self.client.post(
            '/sso/logout', data='', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

    def test_malformed_token_returns_400(self):
        response = self.client.post(
            '/sso/logout',
            data='logout_token=not-a-jwt',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_sid_is_idempotent_200(self):
        payload = {'sid': 'no-such-session'}
        b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        response = self.client.post(
            '/sso/logout',
            data=f'logout_token=h.{b64}.s',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
