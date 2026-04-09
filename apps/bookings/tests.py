from datetime import date

from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.bookings.models import BookingRequest
from apps.projects.models import Project


class BookingPageTests(TestCase):
    def test_booking_page_renders(self):
        response = self.client.get(reverse("bookings:create"))

        self.assertEqual(response.status_code, 200)

    def test_demo_booking_page_prefills_demo_service(self):
        response = self.client.get(
            reverse("bookings:create") + "?service=Client+Portal+Demo"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Schedule a SudPix portal walkthrough")
        self.assertContains(response, 'value="Client Portal Demo"', html=False)
        self.assertContains(response, "Submit Demo Request")

    def test_logged_in_client_booking_page_uses_account_details(self):
        client_user = get_user_model().objects.create_user(
            username="portalclient",
            email="portalclient@example.com",
            password="StrongPass123!",
            first_name="Portal",
            last_name="Client",
        )
        self.client.force_login(client_user)

        response = self.client.get(reverse("bookings:create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Booking As Portal Client")
        self.assertContains(response, "portalclient@example.com")
        self.assertNotContains(response, 'for="id_client_name"', html=False)
        self.assertNotContains(response, 'for="id_email"', html=False)
        self.assertNotContains(response, 'for="id_phone"', html=False)

    def test_booking_post_creates_request_and_redirects_with_success_message(self):
        response = self.client.post(
            reverse("bookings:create"),
            {
                "service": BookingRequest.Service.PHOTOGRAPHY,
                "client_name": "Jane Client",
                "email": "jane@example.com",
                "phone": "+254700000000",
                "event_date": "2026-04-10",
                "notes": "Wedding photography coverage for a full day event.",
            },
        )

        self.assertRedirects(response, reverse("bookings:create"))
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Your booking request has been submitted successfully.", messages)
        booking_request = BookingRequest.objects.get()
        self.assertEqual(booking_request.client_name, "Jane Client")
        self.assertEqual(booking_request.status, BookingRequest.Status.NEW)

    def test_logged_in_client_booking_post_uses_account_details_automatically(self):
        client_user = get_user_model().objects.create_user(
            username="portalclient",
            email="portalclient@example.com",
            password="StrongPass123!",
            first_name="Portal",
            last_name="Client",
        )
        self.client.force_login(client_user)

        response = self.client.post(
            reverse("bookings:create"),
            {
                "service": BookingRequest.Service.VIDEOGRAPHY,
                "event_date": "2026-04-11",
                "notes": "Need a short launch film.",
            },
        )

        self.assertRedirects(response, reverse("bookings:create"))
        booking_request = BookingRequest.objects.get()
        self.assertEqual(booking_request.client_account, client_user)
        self.assertEqual(booking_request.client_name, "Portal Client")
        self.assertEqual(booking_request.email, "portalclient@example.com")
        self.assertEqual(booking_request.phone, "")
        self.assertEqual(booking_request.service, BookingRequest.Service.VIDEOGRAPHY)

    def test_booking_post_with_invalid_data_shows_form_errors(self):
        response = self.client.post(
            reverse("bookings:create"),
            {
                "service": "",
                "client_name": "",
                "email": "not-an-email",
                "phone": "",
                "event_date": "",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BookingRequest.objects.count(), 0)
        self.assertContains(response, "This field is required.")

    def test_confirmed_booking_can_be_converted_to_project(self):
        booking_request = BookingRequest.objects.create(
            service=BookingRequest.Service.BRANDING,
            client_name="Mary Wanjiku",
            email="mary@example.com",
            phone="+254700000001",
            event_date=date(2026, 5, 5),
            notes="Create a complete brand identity package.",
            status=BookingRequest.Status.CONFIRMED,
        )

        project = booking_request.convert_to_project()

        booking_request.refresh_from_db()
        self.assertEqual(booking_request.status, BookingRequest.Status.CONVERTED)
        self.assertEqual(booking_request.converted_project, project)
        self.assertEqual(project.service_type, BookingRequest.Service.BRANDING)
        self.assertEqual(project.status, Project.Status.PENDING)
        self.assertEqual(project.client.email, "mary@example.com")
        self.assertTrue(project.client.has_usable_password() is False)

    def test_confirmed_booking_uses_existing_user_by_email_when_converted(self):
        existing_user = get_user_model().objects.create_user(
            username="existingclient",
            email="existing@example.com",
            password="StrongPass123!",
        )
        booking_request = BookingRequest.objects.create(
            service=BookingRequest.Service.VIDEOGRAPHY,
            client_name="Existing Client",
            email="existing@example.com",
            phone="+254700000002",
            event_date=date(2026, 6, 1),
            notes="Need an event recap film.",
            status=BookingRequest.Status.CONFIRMED,
        )

        project = booking_request.convert_to_project()

        self.assertEqual(project.client, existing_user)

    def test_only_confirmed_booking_can_be_converted(self):
        booking_request = BookingRequest.objects.create(
            service=BookingRequest.Service.PHOTOGRAPHY,
            client_name="Pending Client",
            email="pending@example.com",
            phone="+254700000003",
            event_date=date(2026, 7, 1),
            notes="Portrait session inquiry.",
            status=BookingRequest.Status.NEW,
        )

        with self.assertRaises(ValidationError):
            booking_request.convert_to_project()
