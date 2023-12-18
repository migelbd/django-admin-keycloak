from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django_admin_keycloak.models import KeycloakProvider

admin.site.login_template = 'django_admin_keycloak/login.html'


@admin.register(KeycloakProvider)
class KeycloakProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'active',)
    list_display_links = ('name',)

    fieldsets = (
        (None, {'fields': (
            'active',
            'slug',
            'name',
        )}),
        (_('Server'), {'fields': (
            'server_url',
            'realm_name',
            'client_id',
            'client_secret_key',
        )}),
        (_('Other Info'), {'fields': (
            'redirect_uri',
            'role_super_user',
            'role_staff_user',
            'options',
        )})
    )

    search_fields = ('name', 'slug')
