from django.contrib.sessions.backends.cache import SessionStore as CacheStore


class SessionStore(CacheStore):
    cache_key_prefix = 'django_admin_keycloak.session'
