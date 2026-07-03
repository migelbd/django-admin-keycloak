"""#8 / #10 — session persistence: non-UUID sid works, missing sid is skipped."""
from importlib import import_module

from django.conf import settings
from django.test import RequestFactory, TestCase

from django_admin_keycloak.models import KeycloakSession
from django_admin_keycloak.utils import save_sso_session

from .common import User, make_provider


class SaveSsoSessionTests(TestCase):
    def _request(self, user):
        request = RequestFactory().get('/')
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        request.session.create()
        request.user = user
        return request

    def test_non_uuid_sid_is_stored(self):
        provider = make_provider()
        user = User.objects.create_user('u')
        request = self._request(user)
        session = save_sso_session(request, provider, 'UE-TZhQzFf6LY7aVuZqQT7iR')
        self.assertIsNotNone(session)
        self.assertTrue(
            KeycloakSession.objects.filter(pk='UE-TZhQzFf6LY7aVuZqQT7iR').exists())

    def test_missing_sid_is_skipped_without_crash(self):
        provider = make_provider()
        user = User.objects.create_user('u')
        request = self._request(user)
        session = save_sso_session(request, provider, None)
        self.assertIsNone(session)
        self.assertEqual(KeycloakSession.objects.count(), 0)
        self.assertEqual(request.session['keycloak_pk'], provider.pk)
