from django.contrib.sessions.backends.cache import SessionStore as CacheStore


class SessionStore(CacheStore):
    cache_key_prefix = 'django_admin_keycloak.session'

    def __init__(self, session_key=None):
        super().__init__(session_key)
        self._sid = None

    @property
    def sid(self):
        return self._sid

    @sid.setter
    def sid(self, value):
        self._sid = value
