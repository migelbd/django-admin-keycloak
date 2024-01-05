# django-admin-keycloak

![](https://github.com/migelbd/django-admin-keycloak/raw/main/example.png)

## Keycloak
Create Client OpenID with callback url `https://keycloak.example.ru/sso/*`
add client scopes "roles" and 
set client Backchannel logout URL `https://keycloak.example.ru/sso/logout`
### Settings 
```python

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
Add to INSTALLED_APPS
```python
INSTALLED_APPS = [
    'django_admin_keycloak',
    'django.contrib.admin',
    # ...
]
```
Add to urls.py
```python
urlpatterns = [
    # ...,
    path('sso/', include('django_admin_keycloak.url')),
    # ...
]
```

If you define static config, you must execute command for update providers.
```bash
python manage.py update_static_providers
```
## Available signals
### user_sso_login
###### On login SSO user
- session: KeycloakSession
- request: HttpRequest
- userinfo: dict
- access_token: str
#### user_sso_logout
###### On logout SSO user
- session: KeycloakSession
- request: HttpRequest
