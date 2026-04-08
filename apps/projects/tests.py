from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import build_client_upload_folder_slug, ensure_client_upload_folder


class ProjectFolderTests(TestCase):
    def test_ensure_client_upload_folder_creates_one_default_folder_per_client(self):
        client = get_user_model().objects.create_user(
            username="folderclient",
            email="folder@example.com",
            password="StrongPass123!",
            first_name="Folder",
            last_name="Client",
        )

        first_folder = ensure_client_upload_folder(client)
        second_folder = ensure_client_upload_folder(client)

        self.assertEqual(first_folder.pk, second_folder.pk)
        self.assertEqual(first_folder.slug, build_client_upload_folder_slug(client))
        self.assertEqual(first_folder.title, "Folder Client Files")
