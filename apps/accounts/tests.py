from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.notifications.models import AdminNotification
from apps.projects.models import Project, build_client_upload_folder_slug


class AccountPageTests(TestCase):
    def test_login_page_renders(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose how you want to log in")
        self.assertContains(response, reverse("accounts:client_login"))
        self.assertContains(response, reverse("accounts:admin_login"))

    def test_client_login_page_renders(self):
        response = self.client.get(reverse("accounts:client_login"))

        self.assertEqual(response.status_code, 200)

    def test_admin_login_page_renders(self):
        response = self.client.get(reverse("accounts:admin_login"))

        self.assertEqual(response.status_code, 200)

    def test_register_page_renders(self):
        response = self.client.get(reverse("accounts:register"))

        self.assertEqual(response.status_code, 200)

    def test_password_reset_page_renders(self):
        response = self.client.get(reverse("accounts:password_reset"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recover your client or admin account")

    def test_register_creates_user_and_logs_them_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Portal",
                "last_name": "User",
                "username": "portaluser",
                "email": "portal@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("client:dashboard"))
        user = get_user_model().objects.get(username="portaluser")
        self.assertTrue(get_user_model().objects.filter(username="portaluser").exists())
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(user.pk))
        self.assertTrue(
            Project.objects.filter(
                client=user,
                slug=build_client_upload_folder_slug(user),
            ).exists()
        )
        self.assertTrue(
            AdminNotification.objects.filter(
                kind=AdminNotification.Kind.CLIENT_REGISTERED,
                related_user=user,
            ).exists()
        )

    def test_login_accepts_email_address(self):
        user = get_user_model().objects.create_user(
            username="portaluser",
            email="portal@example.com",
            password="testpass123",
        )

        response = self.client.post(
            reverse("accounts:client_login"),
            {"username": user.email, "password": "testpass123"},
        )

        self.assertRedirects(response, reverse("client:dashboard"))

    def test_login_rejects_ambiguous_shared_email(self):
        get_user_model().objects.create_user(
            username="clientone",
            email="shared@example.com",
            password="testpass123",
        )
        get_user_model().objects.create_user(
            username="clienttwo",
            email="shared@example.com",
            password="testpass456",
        )

        response = self.client.post(
            reverse("accounts:client_login"),
            {"username": "shared@example.com", "password": "testpass123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Multiple accounts use this email address. Please log in with your username instead.",
        )

    def test_admin_login_accepts_staff_user_and_redirects_to_staff_dashboard(self):
        staff_user = get_user_model().objects.create_superuser(
            username="studioadmin",
            email="studioadmin@example.com",
            password="adminpass123",
        )

        response = self.client.post(
            reverse("accounts:admin_login"),
            {"username": staff_user.username, "password": "adminpass123"},
        )

        self.assertRedirects(response, reverse("dashboard:home"))

    def test_admin_login_rejects_non_staff_user(self):
        client_user = get_user_model().objects.create_user(
            username="portaluser",
            email="portal@example.com",
            password="testpass123",
        )

        response = self.client.post(
            reverse("accounts:admin_login"),
            {"username": client_user.username, "password": "testpass123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "reserved for SudPix administrators only")

    def test_password_reset_sends_email_for_client_user(self):
        user = get_user_model().objects.create_user(
            username="portaluser",
            email="portal@example.com",
            password="testpass123",
        )

        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": user.email},
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            reverse("accounts:password_reset_confirm", args=[uid, token]),
            mail.outbox[0].body,
        )

    def test_password_reset_sends_email_for_staff_user(self):
        staff_user = get_user_model().objects.create_superuser(
            username="studioadmin",
            email="studioadmin@example.com",
            password="adminpass123",
        )

        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": staff_user.email},
        )

        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reset your SudPix password", mail.outbox[0].subject)

    def test_password_reset_confirm_updates_password(self):
        user = get_user_model().objects.create_user(
            username="portaluser",
            email="portal@example.com",
            password="testpass123",
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        redirect_response = self.client.get(
            reverse("accounts:password_reset_confirm", args=[uid, token]),
        )

        response = self.client.post(
            redirect_response.url,
            {
                "new_password1": "NewStrongPass123!",
                "new_password2": "NewStrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("accounts:password_reset_complete"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPass123!"))

    def test_profile_page_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:profile')}",
        )

    def test_logout_redirects_to_home_page(self):
        user = get_user_model().objects.create_user(
            username="portaluser",
            password="testpass123",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("core:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_profile_page_renders_for_authenticated_user(self):
        user = get_user_model().objects.create_user(
            username="portaluser",
            password="testpass123",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 200)
