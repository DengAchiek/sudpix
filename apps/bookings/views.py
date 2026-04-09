from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import BookingRequestForm
from .models import BookingRequest


class BookingCreateView(SuccessMessageMixin, CreateView):
    form_class = BookingRequestForm
    model = BookingRequest
    template_name = "bookings/create.html"
    success_url = reverse_lazy("bookings:create")
    success_message = "Your booking request has been submitted successfully."

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
