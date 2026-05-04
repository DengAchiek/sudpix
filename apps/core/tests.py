import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.cart.models import CartItem
from apps.core.models import HeroCarousel, HeroCarouselSlide
from apps.downloads.models import Download
from apps.media_management.models import MediaAsset
from apps.payments.models import Payment
from apps.projects.models import Project

ONE_PIXEL_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00"
    b"\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class CorePageTests(TestCase):
    def test_core_pages_render(self):
        for route_name in ("core:home", "core:about", "core:contact", "core:faq"):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)

    def test_root_favicon_redirects_to_static_icon(self):
        response = self.client.get(reverse("favicon"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/static/favicon.ico?v=20260412d")

    def test_shared_layout_uses_sudpix_logo_for_tab_icon(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '/static/favicon.ico?v=20260412d',
            html=False,
        )

    def test_home_service_cards_link_to_matching_service_pages(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("services:detail", args=["photography"]))
        self.assertContains(response, reverse("services:detail", args=["videography"]))
        self.assertContains(response, reverse("services:detail", args=["branding"]))
        self.assertContains(response, reverse("services:detail", args=["graphic-design"]))

    def test_home_featured_portfolio_cards_link_to_project_pages(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("portfolio:detail", args=["wedding-story"]))
        self.assertContains(response, reverse("portfolio:detail", args=["corporate-campaign"]))
        self.assertContains(response, reverse("portfolio:detail", args=["live-event-film"]))

    def test_shared_navigation_uses_about_link_and_keeps_booking_cta(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{reverse("core:about")}"', html=False)
        self.assertContains(response, ">About<", html=False)
        self.assertContains(response, f'href="{reverse("bookings:create")}"', html=False)
        self.assertContains(response, "Book a Service")

    def test_home_gallery_section_shows_photo_and_video_media(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Media Gallery")
        self.assertContains(response, "Photo Gallery")
        self.assertContains(response, "Video Gallery")
        self.assertContains(response, "Couple portraits")
        self.assertContains(response, "Main recap cut")
        self.assertContains(response, reverse("portfolio:detail", args=["wedding-story"]))
        self.assertContains(response, reverse("portfolio:detail", args=["live-event-film"]))

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
        self.assertContains(response, "sudpix4@gmail.com")
        self.assertContains(response, "+254 768 774 232")
        self.assertContains(response, "Nairobi, Kenya")
        self.assertContains(response, reverse("bookings:create"))
        self.assertContains(
            response,
            f'{reverse("bookings:create")}?service=Client+Portal+Demo',
            html=False,
        )

    def test_about_page_shows_story_and_process_sections(self):
        response = self.client.get(reverse("core:about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About Us")
        self.assertContains(response, "Who We Are")
        self.assertContains(response, "View Our Work")
        self.assertContains(response, "Our Process")
        self.assertContains(response, "Discussion")
        self.assertContains(response, "Follow Up")


class HeroCarouselAdminTests(TestCase):
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

    def _uploaded_slide(self, name="hero.gif"):
        return SimpleUploadedFile(name, ONE_PIXEL_GIF, content_type="image/gif")

    def test_homepage_hero_uses_admin_uploaded_carousel_slide(self):
        carousel = HeroCarousel.objects.create(section_key=HeroCarousel.Section.HOME_MAIN)
        HeroCarouselSlide.objects.create(
            carousel=carousel,
            image=self._uploaded_slide(),
            alt_text="Homepage hero",
            display_order=0,
        )

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/media/hero_carousels/")


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
