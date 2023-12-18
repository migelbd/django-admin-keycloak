# django-admin-keycloak


### Settings 
```python
KEYCLOAK_CONFIG = {
    'enabled': True,
    'name': 'OIDC', # name in link
    'redirect_url': '/',  # redirect url if user not staff
    'superuser_role': 'django_super_user',
    'staff_role': 'django_staff_user',
    'options': {
        'server_url': 'http://keycloak:port',
        'client_id': '<CLIENT_ID>',
        'realm_name': '<REALM_NAME>',
        'client_secret_key': '<TOKEN>',
    }
}


```
