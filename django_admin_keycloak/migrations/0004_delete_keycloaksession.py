# Generated by Django 4.2.9 on 2024-01-04 22:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("django_admin_keycloak", "0003_keycloaksession"),
    ]

    operations = [
        migrations.DeleteModel(
            name="KeycloakSession",
        ),
    ]