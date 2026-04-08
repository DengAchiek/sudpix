from datetime import date
from decimal import Decimal
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.cart.models import CartItem
from apps.dashboard.models import DownloadEvent
from apps.media_management.models import MediaAsset
from apps.payments.models import Payment
from apps.projects.models import Project


class ClientPortalTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.media_override = self.settings(
            MEDIA_ROOT=self.temp_media.name,
            MEDIA_URL="/media/",
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.temp_media.cleanup)

        self.user = get_user_model().objects.create_user(
            username="clientuser",
            email="client@example.com",
            password="testpass123",
            first_name="Client",
            last_name="User",
        )
        self.locked_project = Project.objects.create(
            client=self.user,
            title="Brand Campaign",
            slug="brand-campaign",
            service_type="Branding",
            status=Project.Status.IN_REVIEW,
            shoot_date=date(2026, 3, 16),
            description="Track ongoing branding files and completed design packs.",
        )
        self.unlocked_project = Project.objects.create(
            client=self.user,
            title="Event Recap Film",
            slug="event-recap-film",
            service_type="Videography",
            status=Project.Status.PROCESSING,
            shoot_date=date(2026, 3, 10),
            description="Final recap film currently in post-production.",
        )
        self.locked_photo = MediaAsset.objects.create(
            project=self.locked_project,
            title="Brand Cover 01.jpg",
            kind=MediaAsset.Kind.PHOTO,
            price=Decimal("150.00"),
            file=SimpleUploadedFile(
                "brand-cover-01.jpg",
                b"brand-photo-binary",
                content_type="image/jpeg",
            ),
        )
        self.locked_video = MediaAsset.objects.create(
            project=self.locked_project,
            title="Launch Reel.mp4",
            kind=MediaAsset.Kind.VIDEO,
            price=Decimal("999.00"),
            file=SimpleUploadedFile(
                "launch-reel.mp4",
                b"launch-video-binary",
                content_type="video/mp4",
            ),
        )
        self.unlocked_photo = MediaAsset.objects.create(
            project=self.unlocked_project,
            title="Final Portrait.jpg",
            kind=MediaAsset.Kind.PHOTO,
            price=Decimal("300.00"),
            file=SimpleUploadedFile(
                "final-portrait.jpg",
                b"final-portrait-binary",
                content_type="image/jpeg",
            ),
        )
        self.confirmed_payment = Payment.objects.create(
            user=self.user,
            project=self.unlocked_project,
            amount=Decimal("80.00"),
            method=Payment.Method.MPESA,
            status=Payment.Status.CONFIRMED,
        )
        self.confirmed_payment.media_assets.add(self.unlocked_photo)

    def test_client_portal_requires_login(self):
        response = self.client.get(reverse("client:dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('client:dashboard')}",
        )

    def test_client_portal_pages_render_for_authenticated_user(self):
        self.client.force_login(self.user)

        for route_name in ("client:dashboard", "client:files", "client:cart", "client:checkout", "client:payments", "client:downloads"):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)

    def test_files_page_shows_selection_actions_and_hides_item_prices(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("client:files"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Photos & Videos")
        self.assertContains(response, "data-gallery-form")
        self.assertContains(response, f'aria-label="Select {self.locked_photo.title} for download"', html=False)
        self.assertContains(response, f'aria-label="Select {self.locked_video.title} for download"', html=False)
        self.assertContains(response, f'aria-label="Download {self.unlocked_photo.title}"', html=False)
        self.assertContains(response, "Download Selection")
        self.assertNotContains(response, "Select File")
        self.assertNotContains(response, "KES 80")
        self.assertNotContains(response, "KES 500")

    def test_projects_route_redirects_to_uploaded_media_library(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("client:projects"))

        self.assertRedirects(response, reverse("client:files"))

    def test_project_detail_uses_requested_slug(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("client:project_detail", args=["brand-campaign"]))

        self.assertRedirects(response, f"{reverse('client:files')}?project=brand-campaign")

    def test_unknown_project_slug_returns_404(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("client:project_detail", args=["missing-project"]))

        self.assertEqual(response.status_code, 404)

    def test_select_and_remove_routes_manage_cart_items(self):
        self.client.force_login(self.user)

        select_response = self.client.post(reverse("client:select_file", args=[self.locked_photo.id]))
        self.assertRedirects(select_response, reverse("client:files"))
        self.assertTrue(CartItem.objects.filter(user=self.user, media_asset=self.locked_photo).exists())

        remove_response = self.client.post(reverse("client:remove_file", args=[self.locked_photo.id]))
        self.assertRedirects(remove_response, reverse("client:files"))
        self.assertFalse(CartItem.objects.filter(user=self.user, media_asset=self.locked_photo).exists())

    def test_async_selection_toggle_returns_json_payload_for_gallery(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("client:select_file", args=[self.locked_photo.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "selected": True,
                "selected_files_count": 1,
                "selected_photo_count": 1,
                "selected_video_count": 0,
                "created": True,
            },
        )
        self.assertTrue(CartItem.objects.filter(user=self.user, media_asset=self.locked_photo).exists())

    def test_cart_route_shows_selected_files_and_total(self):
        self.client.force_login(self.user)
        CartItem.objects.create(user=self.user, media_asset=self.locked_photo)
        CartItem.objects.create(user=self.user, media_asset=self.locked_video)

        response = self.client.get(reverse("client:cart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.locked_photo.title)
        self.assertContains(response, self.locked_video.title)
        self.assertContains(response, "KES 580")
        self.assertNotContains(response, "KES 80")
        self.assertNotContains(response, "KES 500")
        self.assertContains(response, ">Download<", html=False)

    def test_checkout_page_uses_download_call_to_action(self):
        self.client.force_login(self.user)
        CartItem.objects.create(user=self.user, media_asset=self.locked_photo)

        response = self.client.get(reverse("client:checkout"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Press Download below to start payment")
        self.assertContains(response, ">Download<", html=False)
        self.assertNotContains(response, "Submit Payment Request")
        self.assertContains(response, "M-Pesa")
        self.assertNotContains(response, ">Card<", html=False)
        self.assertContains(response, "Your M-Pesa phone number")
        self.assertContains(response, "funds are sent to SudPix")

    def test_checkout_rejects_unsupported_manual_payment_methods(self):
        self.client.force_login(self.user)
        CartItem.objects.create(user=self.user, media_asset=self.locked_photo)

        response = self.client.post(
            reverse("client:checkout"),
            {
                "payment_method": Payment.Method.CARD,
                "phone_number": "254700000000",
            },
        )

        self.assertRedirects(response, reverse("client:checkout"))
        self.assertEqual(Payment.objects.exclude(pk=self.confirmed_payment.pk).count(), 0)
        self.assertTrue(CartItem.objects.filter(user=self.user, media_asset=self.locked_photo).exists())

    @patch("apps.clients.views.initiate_stk_push")
    def test_checkout_mpesa_sends_phone_prompt(self, mock_initiate_stk_push):
        mock_initiate_stk_push.return_value = {
            "CheckoutRequestID": "checkout-123",
            "ResponseCode": "0",
        }
        self.client.force_login(self.user)
        CartItem.objects.create(user=self.user, media_asset=self.locked_photo)
        mpesa_settings = self.settings(
            MPESA_CONSUMER_KEY="test-key",
            MPESA_CONSUMER_SECRET="test-secret",
            MPESA_SHORTCODE="174379",
            MPESA_PASSKEY="test-passkey",
            MPESA_CALLBACK_BASE_URL="https://example.com",
        )
        mpesa_settings.enable()
        self.addCleanup(mpesa_settings.disable)

        response = self.client.post(
            reverse("client:checkout"),
            {
                "payment_method": Payment.Method.MPESA,
                "phone_number": "0712345678",
            },
        )

        payment = Payment.objects.exclude(pk=self.confirmed_payment.pk).get()
        self.assertRedirects(response, reverse("client:payment_processing", args=[payment.pk]))
        self.assertEqual(payment.method, Payment.Method.MPESA)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.phone_number, "254712345678")
        mock_initiate_stk_push.assert_called_once()
        self.assertFalse(CartItem.objects.filter(user=self.user).exists())

    @patch("apps.clients.views.initiate_stk_push")
    def test_checkout_requires_client_mpesa_phone_number(self, mock_initiate_stk_push):
        self.client.force_login(self.user)
        CartItem.objects.create(user=self.user, media_asset=self.locked_photo)
        mpesa_settings = self.settings(
            MPESA_CONSUMER_KEY="test-key",
            MPESA_CONSUMER_SECRET="test-secret",
            MPESA_SHORTCODE="174379",
            MPESA_PASSKEY="test-passkey",
            MPESA_CALLBACK_BASE_URL="https://example.com",
        )
        mpesa_settings.enable()
        self.addCleanup(mpesa_settings.disable)

        response = self.client.post(
            reverse("client:checkout"),
            {
                "payment_method": Payment.Method.MPESA,
                "phone_number": "",
            },
        )

        self.assertRedirects(response, reverse("client:checkout"))
        self.assertEqual(Payment.objects.exclude(pk=self.confirmed_payment.pk).count(), 0)
        mock_initiate_stk_push.assert_not_called()

    def test_payment_processing_page_renders_for_payment_owner(self):
        self.client.force_login(self.user)
        processing_payment = Payment.objects.create(
            user=self.user,
            project=self.locked_project,
            amount=Decimal("80.00"),
            method=Payment.Method.MPESA,
            status=Payment.Status.PENDING,
            phone_number="254712345678",
        )
        processing_payment.media_assets.add(self.locked_photo)

        response = self.client.get(reverse("client:payment_processing", args=[processing_payment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Complete payment to unlock your download")
        self.assertContains(response, "Resend M-Pesa Prompt")
        self.assertContains(response, self.locked_photo.title)

    def test_payment_status_endpoint_returns_owner_payment_state(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("client:payment_status", args=[self.confirmed_payment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], Payment.Status.CONFIRMED)
        self.assertTrue(response.json()["download_ready"])

    def test_checkout_mpesa_requires_configuration_before_creating_payment(self):
        self.client.force_login(self.user)
        CartItem.objects.create(user=self.user, media_asset=self.locked_photo)

        response = self.client.post(
            reverse("client:checkout"),
            {
                "payment_method": Payment.Method.MPESA,
                "phone_number": "0712345678",
            },
        )

        self.assertRedirects(response, reverse("client:checkout"))
        self.assertEqual(Payment.objects.exclude(pk=self.confirmed_payment.pk).count(), 0)
        self.assertTrue(CartItem.objects.filter(user=self.user, media_asset=self.locked_photo).exists())

    def test_files_page_marks_pending_payment_after_checkout(self):
        self.client.force_login(self.user)
        payment = Payment.objects.create(
            user=self.user,
            project=self.locked_project,
            amount=Decimal("580.00"),
            method=Payment.Method.MPESA,
            status=Payment.Status.PENDING,
        )
        payment.media_assets.add(self.locked_photo)

        response = self.client.get(reverse("client:files"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Payment Pending")

    def test_downloads_page_only_shows_paid_selected_media(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("client:downloads"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.unlocked_photo.title)
        self.assertNotContains(response, self.locked_photo.title)
        self.assertNotContains(response, self.locked_video.title)

    def test_download_file_redirects_unpaid_file_to_selection(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("client:download_file", args=[self.locked_photo.id]))

        self.assertRedirects(response, reverse("client:cart"))

    def test_download_file_redirects_pending_payment_to_processing(self):
        self.client.force_login(self.user)
        pending_payment = Payment.objects.create(
            user=self.user,
            project=self.locked_project,
            amount=Decimal("80.00"),
            method=Payment.Method.MPESA,
            status=Payment.Status.PENDING,
            phone_number="254712345678",
        )
        pending_payment.media_assets.add(self.locked_photo)

        response = self.client.get(reverse("client:download_file", args=[self.locked_photo.id]))

        self.assertRedirects(response, reverse("client:payment_processing", args=[pending_payment.pk]))

    def test_download_file_returns_uploaded_asset_for_unlocked_owner(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("client:download_file", args=[self.unlocked_photo.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment; filename="final-portrait.jpg"', response["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content), b"final-portrait-binary")
        self.assertTrue(
            DownloadEvent.objects.filter(user=self.user, media_asset=self.unlocked_photo).exists()
        )

    def test_download_file_is_scoped_to_logged_in_client(self):
        other_user = get_user_model().objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="testpass123",
        )
        self.client.force_login(other_user)

        response = self.client.get(reverse("client:download_file", args=[self.unlocked_photo.id]))

        self.assertEqual(response.status_code, 404)

    def test_selecting_unlocked_file_redirects_to_downloads(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("client:select_file", args=[self.unlocked_photo.id]))

        self.assertRedirects(response, reverse("client:downloads"))
        self.assertFalse(CartItem.objects.filter(user=self.user, media_asset=self.unlocked_photo).exists())
