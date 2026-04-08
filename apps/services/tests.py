from django.test import TestCase
from django.urls import reverse

from .models import Service, ServicePackage


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

    def test_service_price_changes_are_reflected_from_database(self):
        service = Service.objects.get(slug="photography")
        package = service.packages.get(name="Starter Shoot")
        package.price_label = "KES 99,000"
        package.save()

        response = self.client.get(reverse("services:detail", args=["photography"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KES 99,000")
        self.assertNotContains(response, "KES 12,000")

    def test_services_page_handles_empty_database(self):
        ServicePackage.objects.all().delete()
        Service.objects.all().delete()

        response = self.client.get(reverse("services:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No services are published yet")
