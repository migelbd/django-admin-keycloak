"""#2 / #6 / #7 / #9 — user provisioning, privilege flags and group sync."""
from django.contrib.auth.models import Group
from django.test import TestCase

from django_admin_keycloak import oidc
from django_admin_keycloak.models import KeycloakUser

from .common import User, make_provider


class CreateUserTests(TestCase):
    """#2 (no account takeover) and #6 (no KeyError on missing optional claims)."""

    def setUp(self):
        self.provider = make_provider()

    def test_new_user_without_optional_claims(self):
        user = oidc.create_user(self.provider, {'preferred_username': 'newbie'})
        self.assertEqual(user.username, 'newbie')
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')

    def test_collision_with_local_account_is_refused(self):
        victim = User.objects.create_superuser('admin', 'admin@example.com', 'pw')
        with self.assertRaises(oidc.KeycloakLoginError):
            oidc.create_user(self.provider, {'preferred_username': 'admin'})
        victim.refresh_from_db()
        self.assertTrue(victim.is_superuser)

    def test_linked_keycloak_user_is_matched(self):
        linked = User.objects.create_user('linked')
        KeycloakUser.objects.create(
            provider=self.provider, user=linked, preferred_username='linked', raw_data={})
        got = oidc.create_user(self.provider, {'preferred_username': 'linked'})
        self.assertEqual(got.pk, linked.pk)

    def test_link_is_provider_scoped(self):
        linked = User.objects.create_user('linked')
        KeycloakUser.objects.create(
            provider=self.provider, user=linked, preferred_username='linked', raw_data={})
        other = make_provider(slug='p2', client_id='c2', realm_name='r2')
        with self.assertRaises(oidc.KeycloakLoginError):
            oidc.create_user(other, {'preferred_username': 'linked'})


class CheckPermissionsTests(TestCase):
    """#7 — revoke on empty groups, leave untouched when the claim is absent."""

    def setUp(self):
        self.provider = make_provider()

    def test_absent_groups_claim_leaves_flags_untouched(self):
        user = User.objects.create_user('u', is_staff=True, is_superuser=True)
        oidc.check_permissions(self.provider, user, {})  # no 'groups' key
        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_empty_groups_revoke_privileges(self):
        user = User.objects.create_user('u', is_staff=True, is_superuser=True)
        oidc.check_permissions(self.provider, user, {'groups': []})
        user.refresh_from_db()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_matching_group_grants_flag(self):
        user = User.objects.create_user('u')
        oidc.check_permissions(self.provider, user, {'groups': ['django-staff']})
        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)


class CheckMemberOfTests(TestCase):
    """#9 — mirror Keycloak groups when present, no-op when the claim is absent."""

    def setUp(self):
        self.provider = make_provider()
        self.g1 = Group.objects.create(name='g1')
        self.g2 = Group.objects.create(name='g2')

    def test_present_claim_replaces_membership(self):
        user = User.objects.create_user('u')
        user.groups.add(self.g2)  # manually assigned
        oidc.check_member_of(self.provider, user, {'groups': ['g1']})
        self.assertEqual(set(user.groups.values_list('name', flat=True)), {'g1'})

    def test_absent_claim_is_noop(self):
        user = User.objects.create_user('u')
        user.groups.add(self.g2)
        oidc.check_member_of(self.provider, user, {})
        self.assertEqual(set(user.groups.values_list('name', flat=True)), {'g2'})
