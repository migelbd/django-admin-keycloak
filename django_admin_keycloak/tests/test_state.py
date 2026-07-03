"""#4 — OIDC state used as a single-use CSRF nonce, plus auth_oidc guard clauses."""
from django.test import RequestFactory, SimpleTestCase, TestCase

from django_admin_keycloak import oidc

from .common import DummySession, make_provider


class StateNonceTests(SimpleTestCase):
    def _request(self):
        request = RequestFactory().get('/')
        request.session = DummySession()
        return request

    def test_store_then_pop_roundtrip(self):
        request = self._request()
        state = oidc._store_state(request, '/next-target')
        self.assertEqual(oidc._pop_state(request, state), '/next-target')

    def test_state_is_single_use(self):
        request = self._request()
        state = oidc._store_state(request, '/x')
        oidc._pop_state(request, state)
        self.assertIsNone(oidc._pop_state(request, state))

    def test_forged_state_is_rejected(self):
        request = self._request()
        oidc._store_state(request, '/x')
        self.assertIsNone(oidc._pop_state(request, 'forged'))

    def test_empty_state_is_rejected(self):
        self.assertIsNone(oidc._pop_state(self._request(), None))

    def test_pending_states_are_bounded(self):
        request = self._request()
        last = None
        for _ in range(oidc.MAX_PENDING_STATES + 5):
            last = oidc._store_state(request, '/x')
        stored = request.session[oidc.STATE_SESSION_KEY]
        self.assertLessEqual(len(stored), oidc.MAX_PENDING_STATES)
        # the most recent state must survive the bounding reset
        self.assertEqual(oidc._pop_state(request, last), '/x')


class AuthOidcGuardTests(TestCase):
    """auth_oidc must reject bad callbacks before performing any network call."""

    def setUp(self):
        self.provider = make_provider()

    def _request(self, query):
        request = RequestFactory().get('/sso/login/devconf', query)
        request.session = DummySession()
        return request

    def test_missing_code_raises(self):
        request = self._request({'state': 'whatever'})
        with self.assertRaises(oidc.KeycloakLoginError):
            oidc.auth_oidc(self.provider, request)

    def test_unknown_state_raises(self):
        # code present but state was never stored in this session -> reject
        request = self._request({'code': 'abc', 'state': 'never-stored'})
        with self.assertRaises(oidc.KeycloakLoginError):
            oidc.auth_oidc(self.provider, request)
