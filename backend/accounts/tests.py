from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.test import APITestCase

from .models import User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountAuthenticationTests(APITestCase):
    def test_superuser_is_created_with_administrator_role(self):
        user = User.objects.create_superuser(
            username='admin-espace',
            email='admin-espace@example.com',
            password='A-long-safe-password-42!',
        )

        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role, User.ROLE_ADMIN)

    def test_registration_creates_participant_with_hashed_password(self):
        response = self.client.post(reverse('register'), {
            'username': 'new-participant',
            'email': 'participant@example.com',
            'password': 'A-long-safe-password-42!',
        })

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='new-participant')
        self.assertEqual(user.role, User.ROLE_PARTICIPANT)
        self.assertTrue(user.check_password('A-long-safe-password-42!'))
        self.assertNotIn('password', response.data)
        self.assertEqual(user.client_profile.email, 'participant@example.com')

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(
            username='existing',
            email='participant@example.com',
            password='A-long-safe-password-42!',
        )

        response = self.client.post(reverse('register'), {
            'username': 'another-user',
            'email': 'PARTICIPANT@example.com',
            'password': 'A-long-safe-password-42!',
        })

        self.assertEqual(response.status_code, 400)

    def test_registration_rejects_username_shorter_than_three_characters(self):
        response = self.client.post(reverse('register'), {
            'username': 'ab',
            'email': 'participant@example.com',
            'password': 'A-long-safe-password-42!',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.data)

    def test_registration_rejects_username_containing_only_digits(self):
        response = self.client.post(reverse('register'), {
            'username': '123456',
            'email': 'participant@example.com',
            'password': 'A-long-safe-password-42!',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.data)

    def test_registration_rejects_short_first_or_last_name(self):
        for field in ('first_name', 'last_name'):
            with self.subTest(field=field):
                response = self.client.post(reverse('register'), {
                    'username': 'new-participant',
                    'email': 'participant@example.com',
                    'password': 'A-long-safe-password-42!',
                    field: 'ab',
                })

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)

    def test_password_reset_is_generic_and_changes_password(self):
        user = User.objects.create_user(
            username='existing',
            email='participant@example.com',
            password='A-long-safe-password-42!',
        )

        response = self.client.post(reverse('password-reset'), {'email': user.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = self.client.post(reverse('password-reset-confirm'), {
            'uid': uid,
            'token': token,
            'new_password': 'An-even-safer-password-73!',
        })

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('An-even-safer-password-73!'))
        self.assertFalse(default_token_generator.check_token(user, token))

    def test_password_reset_request_does_not_disclose_unknown_email(self):
        response = self.client.post(reverse('password-reset'), {'email': 'unknown@example.com'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_admin_cannot_create_a_client_account(self):
        admin = User.objects.create_user(
            username='admin-create',
            email='admin-create@example.com',
            password='A-long-safe-password-42!',
            role=User.ROLE_ADMIN,
        )
        self.client.force_authenticate(admin)

        response = self.client.post(reverse('user-list'), {
            'username': 'managed-client',
            'email': 'managed-client@example.com',
            'password': 'A-long-safe-password-42!',
            'phone': '0123456789',
            'role': User.ROLE_PARTICIPANT,
        }, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='managed-client').exists())

    def test_admin_user_creation_rejects_phone_with_wrong_length(self):
        admin = User.objects.create_user(
            username='admin-phone',
            email='admin-phone@example.com',
            password='A-long-safe-password-42!',
            role=User.ROLE_ADMIN,
        )
        self.client.force_authenticate(admin)

        response = self.client.post(reverse('user-list'), {
            'username': 'managed-client',
            'email': 'managed-client@example.com',
            'password': 'A-long-safe-password-42!',
            'phone': '123456789',
            'role': User.ROLE_PARTICIPANT,
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('phone', response.data)
        self.assertFalse(User.objects.filter(username='managed-client').exists())

    def test_admin_cannot_change_client_personal_information(self):
        admin = User.objects.create_user(
            username='admin-protect',
            email='admin-protect@example.com',
            password='A-long-safe-password-42!',
            role=User.ROLE_ADMIN,
        )
        client_user = User.objects.create_user(
            username='client-protect',
            email='client-protect@example.com',
            password='A-long-safe-password-42!',
            phone='0123456789',
        )
        self.client.force_authenticate(admin)

        response = self.client.patch(
            reverse('user-detail', args=[client_user.pk]),
            {'phone': '0987654321'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        client_user.refresh_from_db()
        self.assertEqual(client_user.phone, '0123456789')

    def test_admin_cannot_convert_another_account_into_a_client(self):
        admin = User.objects.create_user(
            username='admin-convert',
            email='admin-convert@example.com',
            password='A-long-safe-password-42!',
            role=User.ROLE_ADMIN,
        )
        staff_user = User.objects.create_user(
            username='staff-convert',
            email='staff-convert@example.com',
            password='A-long-safe-password-42!',
            phone='0123456789',
            role=User.ROLE_ORGANIZER,
        )
        self.client.force_authenticate(admin)

        response = self.client.patch(
            reverse('user-detail', args=[staff_user.pk]),
            {'role': User.ROLE_PARTICIPANT},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        staff_user.refresh_from_db()
        self.assertEqual(staff_user.role, User.ROLE_ORGANIZER)
        self.assertFalse(hasattr(staff_user, 'client_profile'))

    def test_user_cannot_promote_own_account_to_admin(self):
        user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='A-long-safe-password-42!',
        )
        self.client.force_authenticate(user)

        response = self.client.patch(
            reverse('user-detail', args=[user.pk]),
            {'role': User.ROLE_ADMIN, 'phone': '0123456789'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        user.refresh_from_db()
        self.assertEqual(user.role, User.ROLE_PARTICIPANT)
