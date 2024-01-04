# django-admin-keycloak

![](/Users/sven/PycharmProjects/django-admin-keycloak/example.png)

### Settings 
```python
# need for Backchannel logout
SESSION_ENGINE = 'django_admin_keycloak.session.db' 
# or django_admin_keycloak.session.cache

# define static config or add provider later in admin management
KEYCLOAK_PROVIDERS = [
    {
        'slug': 'local', # internal django slug
        'name': 'Local', # name on login form
        'client_id': 'local_django',
        'client_secret': 'SECRET',
        'redirect_uri': '/admin', # redirect uri after login
        'server_url': 'https://keycloak.example.ru',
        'realm_name': 'django',
        'role_staff_user': 'dev_staff', # role for staff users
        'role_super_user': 'dev_super_user', # role for superusers
    }
]

```

Add to urls.py
```python
urlpatterns = [
    # ...,
    path('auth/', include('django_admin_keycloak.url')),
    # ...
]
```

If you define static config, you must execute command for update providers.
```bash
python manage.py update_static_providers
```
