import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.views.generic import CreateView

from .forms import BookingRequestForm
from .models import BookingRequest

logger = logging.getLogger(__name__)


class BookingCreateView(CreateView):
    form_class = BookingRequestForm
    model = BookingRequest
    template_name = "bookings/create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        service = self.request.GET.get("service")
        service_choices = {choice for choice, _ in BookingRequest.Service.choices}
        if service in service_choices:
            initial["service"] = service
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")
        selected_service = ""
        if form is not None:
            if form.is_bound:
                selected_service = str(form.data.get("service", "")).strip()
            else:
                selected_service = str(form.initial.get("service", "")).strip()
        is_demo_request = selected_service == BookingRequest.Service.CLIENT_PORTAL_DEMO
        context.update(
            {
                "booking_submitted": self.request.GET.get("submitted") == "1",
                "booking_steps": [
                    "Submit your booking request",
                    "Our team reviews your project scope",
                    "We confirm timeline, package, and pricing",
                    "Production and delivery begin",
                ],
                "requires_client_details": getattr(form, "requires_client_details", True),
                "prefilled_identity": getattr(form, "prefilled_identity", {}),
                "is_demo_request": is_demo_request,
            }
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.send_booking_notification(self.object)
        return response

    def get_success_url(self):
        params = {"submitted": "1"}
        return f"{reverse('bookings:create')}?{urlencode(params)}"

    def send_booking_notification(self, booking_request):
        recipient = getattr(settings, "BOOKING_NOTIFICATION_EMAIL", "").strip()
        if not recipient:
            return

        portal_label = (
            f"Signed-in client: {booking_request.client_account.get_username()}"
            if booking_request.client_account_id
            else "Signed-in client: No"
        )
        subject = f"New SudPix booking request: {booking_request.service}"
        message = "\n".join(
            [
                "A new booking request has been submitted on SudPix.",
                "",
                f"Client: {booking_request.client_name}",
                f"Email: {booking_request.email}",
                f"Phone: {booking_request.phone or 'Not provided'}",
                f"Service: {booking_request.service}",
                f"Event/Project date: {booking_request.event_date}",
                portal_label,
                "",
                "Project notes:",
                booking_request.notes,
            ]
        )

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )
        except Exception:
            logger.exception(
                "Failed to send booking notification email for booking %s",
                booking_request.pk,
            )
