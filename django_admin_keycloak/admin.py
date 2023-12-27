from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django_admin_keycloak.models import KeycloakProvider

admin.site.login_template = 'django_admin_keycloak/login.html'


class KeycloakProviderModelForm(forms.ModelForm):
    class Meta:
        model = KeycloakProvider
        fields = '__all__'
        widgets = {
            'client_secret': forms.PasswordInput()
        }


@admin.register(KeycloakProvider)
class KeycloakProviderAdmin(admin.ModelAdmin):
    form = KeycloakProviderModelForm
    list_display = ('name', 'slug', 'active',)
    list_display_links = ('name',)

    def get_fieldsets(self, request, obj=None):
        server_fields = [
            'server_url',
            'realm_name',
            'client_id',
            'client_secret',
            'scope',
        ]
        if obj and getattr(obj, 'is_static', False):
            server_fields.remove('client_secret')
        return (
            (None, {'fields': (
                'active',
                'slug',
                'name',
            )}),
            (_('Server'), {'fields': server_fields}),
            (_('Other Info'), {'fields': (
                'redirect_uri',
                'role_super_user',
                'role_staff_user',
                'options',
            )})
        )

    def get_exclude(self, request, obj=None):
        excluded = list(super().get_exclude(request, obj) or [])
        if obj and getattr(obj, 'is_static', False):
            return excluded.append('client_secret')
        return excluded

    def has_change_permission(self, request, obj=None):
        if obj and getattr(obj, 'is_static', False):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and getattr(obj, 'is_static', False):
            return False
        return super().has_delete_permission(request, obj)

    search_fields = ('name', 'slug')
