# django-admin-keycloak


### Settings 
```python
KEYCLOAK_PROVIDERS = [
    {
        'slug': 'local',
        'name': 'Local',
        'client_id': 'local_django',
        'client_secret': 'SECRET',
        'redirect_uri': '/admin',
        'server_url': 'https://keycloak.example.ru',
        'realm_name': 'django',
        'role_staff_user': 'dev_staff',
        'role_super_user': 'dev_super_user',
    }
]


```
