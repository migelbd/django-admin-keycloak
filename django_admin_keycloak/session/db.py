from django.contrib.sessions.backends.db import SessionStore as DBStore

from django_admin_keycloak.models import KeycloakSession


class SessionStore(DBStore):

    def __init__(self, session_key=None):
        super().__init__(session_key)
        self._sid = None

    @classmethod
    def get_model_class(cls):
        return KeycloakSession

    def create_model_instance(self, data):
        obj = super().create_model_instance(data)
        obj.sid = self._sid
        return obj

    @property
    def sid(self):
        return self._sid

    @sid.setter
    def sid(self, value):
        self._sid = value


