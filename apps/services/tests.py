from django.test import TestCase
from django.urls import reverse


class ServicesPageTests(TestCase):
    def test_services_page_renders(self):
        response = self.client.get(reverse("services:list"))

        self.assertEqual(response.status_code, 200)
