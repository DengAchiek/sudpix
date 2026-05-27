from io import BytesIO
import tempfile
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.projects.models import Project, ensure_client_upload_folder

from .models import MediaAsset


def uploaded_jpeg(name, size=(1800, 1200)):
    output = BytesIO()
    Image.new("RGB", size, color=(142, 98, 45)).save(output, format="JPEG")
    return SimpleUploadedFile(name, output.getvalue(), content_type="image/jpeg")


class MediaAssetModelTests(TestCase):
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
            username="portalclient",
            email="portalclient@example.com",
            password="testpass123",
        )
        self.project = Project.objects.create(
            client=self.user,
            title="Gallery Delivery",
            slug="gallery-delivery",
            service_type="Photography",
            status=Project.Status.READY,
            shoot_date=date(2026, 3, 20),
        )

    def test_preview_url_never_falls_back_to_unprotected_original(self):
        media_asset = MediaAsset.objects.create(
            project=self.project,
            title="Ceremony Portrait",
            kind=MediaAsset.Kind.PHOTO,
            price=Decimal("0.00"),
            file=SimpleUploadedFile(
                "ceremony-portrait.jpg",
                b"fake-image-binary",
                content_type="image/jpeg",
            ),
        )

        self.assertTrue(media_asset.is_previewable_image)
        self.assertNotEqual(media_asset.preview_url, media_asset.file.url)
        self.assertFalse(media_asset.preview_is_protected)


class MediaAssetAdminTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.media_override = self.settings(
            MEDIA_ROOT=self.temp_media.name,
            MEDIA_URL="/media/",
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.temp_media.cleanup)

        self.admin_user = get_user_model().objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="adminpass123",
        )
        self.client.force_login(self.admin_user)

        self.portal_user = get_user_model().objects.create_user(
            username="weddingclient",
            email="weddingclient@example.com",
            password="testpass123",
        )
        self.project = Project.objects.create(
            client=self.portal_user,
            title="Wedding Gallery",
            slug="wedding-gallery",
            service_type="Photography",
            status=Project.Status.READY,
            shoot_date=date(2026, 3, 21),
        )

    def test_admin_add_form_renders_drag_and_drop_uploader(self):
        response = self.client.get(reverse("admin:media_management_mediaasset_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Client name")
        self.assertContains(response, "Drag and drop many images or videos here")
        self.assertContains(response, 'data-batch-dropzone')
        self.assertNotContains(response, "Price")
        self.assertNotContains(response, "Highlight")
        self.assertNotContains(response, "Edited")

    def test_admin_can_upload_multiple_local_images_for_one_project(self):
        response = self.client.post(
            reverse("admin:media_management_mediaasset_add"),
            {
                "client": self.portal_user.pk,
                "batch_files": [
                    SimpleUploadedFile(
                        "wedding-01.jpg",
                        uploaded_jpeg("source-01.jpg").read(),
                        content_type="image/jpeg",
                    ),
                    SimpleUploadedFile(
                        "wedding-02.jpg",
                        uploaded_jpeg("source-02.jpg").read(),
                        content_type="image/jpeg",
                    ),
                ],
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)
        upload_folder = ensure_client_upload_folder(self.portal_user)
        assets = list(MediaAsset.objects.filter(project=upload_folder).order_by("title"))
        self.assertEqual(len(assets), 2)
        self.assertEqual(assets[0].title, "wedding 01")
        self.assertEqual(assets[1].title, "wedding 02")
        self.assertTrue(all(asset.price == Decimal("80.00") for asset in assets))
        self.assertTrue(all(asset.file for asset in assets))
        self.assertTrue(all(asset.preview_image for asset in assets))
        self.assertTrue(all(asset.preview_is_protected for asset in assets))
        for asset in assets:
            with asset.file.open("rb") as original, asset.preview_image.open("rb") as preview:
                self.assertNotEqual(original.read(), preview.read())

        self.client.logout()
        self.client.force_login(self.portal_user)
        portal_response = self.client.get(f"{reverse('client:files')}?project={upload_folder.slug}")
        self.assertContains(portal_response, "wedding 01")
        self.assertContains(portal_response, "wedding 02")
        self.assertContains(
            portal_response,
            'aria-label="Select wedding 01 for download"',
            html=False,
        )
        self.assertContains(
            portal_response,
            reverse("client:preview_file", args=[assets[0].pk]),
            html=False,
        )
        self.assertNotContains(portal_response, assets[0].file.url, html=False)
