from datetime import date
from decimal import Decimal
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.bookings.models import BookingRequest
from apps.cart.models import CartItem
from apps.media_management.models import MediaAsset
from apps.notifications.models import AdminNotification
from apps.payments.models import Payment
from apps.projects.models import Project, ensure_client_upload_folder

from .models import DownloadEvent


class StaffDashboardTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.media_override = self.settings(
            MEDIA_ROOT=self.temp_media.name,
            MEDIA_URL="/media/",
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.temp_media.cleanup)

        self.staff_user = get_user_model().objects.create_superuser(
            username="studioadmin",
            email="studioadmin@example.com",
            password="adminpass123",
        )
        self.client_user = get_user_model().objects.create_user(
            username="portalclient",
            email="portalclient@example.com",
            password="clientpass123",
        )
        self.project = Project.objects.create(
            client=self.client_user,
            title="Wedding Folder",
            slug="wedding-folder",
            service_type="Photography",
            status=Project.Status.READY,
            shoot_date=date(2026, 3, 28),
        )
        self.media_asset = MediaAsset.objects.create(
            project=self.project,
            title="Ceremony Frame.jpg",
            kind=MediaAsset.Kind.PHOTO,
            file=SimpleUploadedFile(
                "ceremony-frame.jpg",
                b"image-binary",
                content_type="image/jpeg",
            ),
        )
        self.payment = Payment.objects.create(
            user=self.client_user,
            project=self.project,
            amount=Decimal("80.00"),
            method=Payment.Method.MPESA,
            status=Payment.Status.PENDING,
            phone_number="254712345678",
        )
        self.payment.media_assets.add(self.media_asset)
        CartItem.objects.create(user=self.client_user, media_asset=self.media_asset)
        BookingRequest.objects.create(
            service=BookingRequest.Service.PHOTOGRAPHY,
            client_name="Portal Client",
            email="portalclient@example.com",
            phone="254712345678",
            event_date=date(2026, 4, 15),
            notes="Need a full event shoot.",
        )
        DownloadEvent.objects.create(
            user=self.client_user,
            media_asset=self.media_asset,
            payment=self.payment,
        )
        AdminNotification.objects.create(
            kind=AdminNotification.Kind.CLIENT_REGISTERED,
            title="New client registration",
            message="Portal Client just created a SudPix client account.",
            related_user=self.client_user,
        )

    def test_staff_dashboard_requires_staff_access(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:admin_login')}?next={reverse('dashboard:home')}",
        )

        self.client.force_login(self.client_user)
        client_response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(client_response, reverse("client:dashboard"))

    def test_staff_dashboard_renders_client_activity(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "staff/base.html")
        self.assertContains(response, "Client activity and uploads")
        self.assertContains(response, "Separate from the public site layout")
        self.assertContains(response, "Tap any activity card")
        self.assertContains(response, "Show all activity")
        self.assertContains(response, "New Signups")
        self.assertContains(response, "Admin Notifications")
        self.assertContains(response, "Uploaded Gallery")
        self.assertContains(response, "Ceremony Frame.jpg")
        self.assertContains(response, self.media_asset.preview_url)
        self.assertContains(response, "data-preview-modal")
        self.assertContains(response, "Close preview")
        self.assertContains(response, "Portal Client")
        self.assertContains(response, "Pending")
        self.assertContains(response, "Batch Upload")
        self.assertContains(response, "Client name")

    def test_django_admin_has_separate_backend_branding(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SudPix Django Admin")
        self.assertContains(response, "Backend data and user management stay separate")

    def test_staff_can_upload_files_from_site_dashboard(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("dashboard:home"),
            {
                "client": self.client_user.pk,
                "batch_files": [
                    SimpleUploadedFile(
                        "gallery-01.jpg",
                        b"image-one",
                        content_type="image/jpeg",
                    ),
                    SimpleUploadedFile(
                        "gallery-02.mp4",
                        b"video-one",
                        content_type="video/mp4",
                    ),
                ],
            },
        )

        self.assertRedirects(response, reverse("dashboard:home"))
        upload_folder = ensure_client_upload_folder(self.client_user)
        self.assertTrue(MediaAsset.objects.filter(project=upload_folder, title="gallery 01").exists())
        self.assertTrue(MediaAsset.objects.filter(project=upload_folder, title="gallery 02").exists())

        self.client.logout()
        self.client.force_login(self.client_user)
        portal_response = self.client.get(f"{reverse('client:files')}?project={upload_folder.slug}")
        self.assertContains(portal_response, "gallery 01")
        self.assertContains(portal_response, "gallery 02")
