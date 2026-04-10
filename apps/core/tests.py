import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.cart.models import CartItem
from apps.downloads.models import Download
from apps.media_management.models import MediaAsset
from apps.payments.models import Payment
from apps.projects.models import Project


class CorePageTests(TestCase):
    def test_core_pages_render(self):
        for route_name in ("core:home", "core:about", "core:contact", "core:faq"):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)

    def test_root_favicon_redirects_to_static_icon(self):
        response = self.client.get(reverse("favicon"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/static/favicon.ico?v=20260410b")

    def test_home_service_cards_link_to_matching_service_pages(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("services:detail", args=["photography"]))
        self.assertContains(response, reverse("services:detail", args=["videography"]))
        self.assertContains(response, reverse("services:detail", args=["branding"]))
        self.assertContains(response, reverse("services:detail", args=["graphic-design"]))

    def test_home_demo_button_links_to_demo_booking_flow(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'{reverse("bookings:create")}?service=Client+Portal+Demo',
            html=False,
        )

    def test_contact_page_shows_contact_details_and_actions(self):
        response = self.client.get(reverse("core:contact"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hello@sudpix.com")
        self.assertContains(response, "+254 768 774 232")
        self.assertContains(response, "Nairobi, Kenya")
        self.assertContains(response, reverse("bookings:create"))
        self.assertContains(
            response,
            f'{reverse("bookings:create")}?service=Client+Portal+Demo',
            html=False,
        )


class SeedPortalDemoCommandTests(TestCase):
    def setUp(self):
        super().setUp()
        self.temp_media = tempfile.TemporaryDirectory()
        self.media_override = self.settings(
            MEDIA_ROOT=self.temp_media.name,
            MEDIA_URL="/media/",
        )
        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()
        super().tearDown()

    def test_seed_command_creates_repeatable_demo_data(self):
        call_command(
            "seed_portal_demo",
            "--username",
            "seed_demo",
            "--password",
            "SeedDemo123!",
            "--email",
            "seed@example.com",
            "--reset",
        )
        call_command(
            "seed_portal_demo",
            "--username",
            "seed_demo",
            "--password",
            "SeedDemo123!",
            "--email",
            "seed@example.com",
        )

        user = get_user_model().objects.get(username="seed_demo")

        self.assertEqual(Project.objects.filter(client=user).count(), 3)
        self.assertEqual(MediaAsset.objects.filter(project__client=user).count(), 5)
        self.assertEqual(
            MediaAsset.objects.filter(project__client=user).exclude(preview_image="").count(),
            5,
        )
        self.assertEqual(
            MediaAsset.objects.filter(project__client=user).exclude(file="").count(),
            5,
        )
        self.assertEqual(CartItem.objects.filter(user=user).count(), 2)
        self.assertEqual(Payment.objects.filter(user=user).count(), 2)
        self.assertEqual(Download.objects.filter(user=user).count(), 2)
        self.assertEqual(
            Download.objects.filter(user=user).exclude(file="").count(),
            1,
        )
