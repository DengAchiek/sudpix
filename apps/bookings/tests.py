from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.bookings.models import BookingRequest
from apps.notifications.models import AdminNotification
from apps.projects.models import FinalDelivery, Project, ProjectApproval, ProjectBrief, ProjectMilestone


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

    def test_booking_post_creates_request_and_redirects_to_submitted_state(self):
        with self.settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
            BOOKING_NOTIFICATION_EMAIL="sudpix4@gmail.com",
        ):
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

        self.assertRedirects(response, f"{reverse('bookings:create')}?submitted=1")
        booking_request = BookingRequest.objects.get()
        self.assertEqual(booking_request.client_name, "Jane Client")
        self.assertEqual(booking_request.status, BookingRequest.Status.NEW)
        self.assertEqual(booking_request.last_progress_notified_status, BookingRequest.Status.NEW)
        self.assertIsNotNone(booking_request.progress_notified_at)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["sudpix4@gmail.com"])
        self.assertIn("Jane Client", mail.outbox[0].body)
        self.assertEqual(mail.outbox[1].to, ["jane@example.com"])
        self.assertIn("We received your SudPix booking request", mail.outbox[1].subject)
        self.assertIn("Your booking request is in the SudPix queue.", mail.outbox[1].body)
        notification = AdminNotification.objects.get()
        self.assertEqual(notification.kind, AdminNotification.Kind.BOOKING_REQUESTED)
        self.assertIn("Jane Client", notification.message)

    def test_booking_submitted_state_shows_thank_you_panel(self):
        response = self.client.get(f"{reverse('bookings:create')}?submitted=1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thank you for booking with SudPix.")
        self.assertContains(response, "We have sent a confirmation email")
        self.assertContains(response, "email your secure access link automatically")
        self.assertContains(response, "Book Another Service")
        self.assertContains(response, "Browse More Services")
        self.assertNotContains(response, "Submit Booking Request")

    def test_logged_in_client_booking_post_uses_account_details_automatically(self):
        client_user = get_user_model().objects.create_user(
            username="portalclient",
            email="portalclient@example.com",
            password="StrongPass123!",
            first_name="Portal",
            last_name="Client",
        )
        self.client.force_login(client_user)

        with self.settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
            BOOKING_NOTIFICATION_EMAIL="sudpix4@gmail.com",
        ):
            response = self.client.post(
                reverse("bookings:create"),
                {
                    "service": BookingRequest.Service.VIDEOGRAPHY,
                    "event_date": "2026-04-11",
                    "notes": "Need a short launch film.",
                },
            )

        self.assertRedirects(response, f"{reverse('bookings:create')}?submitted=1")
        booking_request = BookingRequest.objects.get()
        self.assertEqual(booking_request.client_account, client_user)
        self.assertEqual(booking_request.client_name, "Portal Client")
        self.assertEqual(booking_request.email, "portalclient@example.com")
        self.assertEqual(booking_request.phone, "")
        self.assertEqual(booking_request.service, BookingRequest.Service.VIDEOGRAPHY)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("Signed-in client: portalclient", mail.outbox[0].body)
        self.assertEqual(mail.outbox[1].to, ["portalclient@example.com"])
        notification = AdminNotification.objects.get()
        self.assertEqual(notification.related_user, client_user)

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
        self.assertTrue(ProjectBrief.objects.filter(project=project).exists())
        self.assertEqual(ProjectMilestone.objects.filter(project=project).count(), 7)
        self.assertTrue(ProjectApproval.objects.filter(project=project).exists())
        self.assertTrue(FinalDelivery.objects.filter(project=project).exists())
        self.assertIsNotNone(booking_request.portal_invite_sent_at)
        self.assertEqual(len(mail.outbox), 1)
        uid = urlsafe_base64_encode(force_bytes(project.client.pk))
        token = default_token_generator.make_token(project.client)
        self.assertIn(reverse("accounts:password_reset_confirm", args=[uid, token]), mail.outbox[0].body)
        self.assertIn(project.title, mail.outbox[0].subject)

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
        booking_request.refresh_from_db()
        self.assertIsNotNone(booking_request.portal_invite_sent_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(project.get_absolute_url(), mail.outbox[0].body)
        self.assertNotIn(reverse("accounts:password_reset"), mail.outbox[0].body)

    def test_booking_progress_status_changes_send_client_updates_once(self):
        booking_request = BookingRequest.objects.create(
            service=BookingRequest.Service.PHOTOGRAPHY,
            client_name="Progress Client",
            email="progress@example.com",
            phone="+254700000004",
            event_date=date(2026, 7, 7),
            notes="Corporate headshots.",
            status=BookingRequest.Status.NEW,
        )

        changed = booking_request.transition_to_status(BookingRequest.Status.CONTACTED)

        booking_request.refresh_from_db()
        self.assertTrue(changed)
        self.assertEqual(booking_request.status, BookingRequest.Status.CONTACTED)
        self.assertEqual(booking_request.last_progress_notified_status, BookingRequest.Status.CONTACTED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("SudPix has started your booking review", mail.outbox[0].subject)
        self.assertIn("Corporate headshots.", mail.outbox[0].body)

        unchanged = booking_request.transition_to_status(BookingRequest.Status.CONTACTED)

        self.assertFalse(unchanged)
        self.assertEqual(len(mail.outbox), 1)

        booking_request.transition_to_status(BookingRequest.Status.QUOTED)

        booking_request.refresh_from_db()
        self.assertEqual(booking_request.last_progress_notified_status, BookingRequest.Status.QUOTED)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("Your SudPix booking has been quoted", mail.outbox[1].subject)

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
