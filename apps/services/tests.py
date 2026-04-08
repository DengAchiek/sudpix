from django.test import TestCase
from django.urls import reverse


class ServicesPageTests(TestCase):
    def test_services_page_renders(self):
        response = self.client.get(reverse("services:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("services:detail", args=["photography"]))
        self.assertContains(response, "Photography Services")

    def test_specific_service_route_renders_selected_service_details(self):
        response = self.client.get(reverse("services:detail", args=["videography"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Videography Services")
        self.assertContains(response, "Brand Story Package")
        self.assertContains(response, f"{reverse('bookings:create')}?service=Videography")

    def test_invalid_service_slug_returns_404(self):
        response = self.client.get(reverse("services:detail", args=["unknown-service"]))

        self.assertEqual(response.status_code, 404)
