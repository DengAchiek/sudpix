from django import forms
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q

from apps.payments.models import Payment

from .models import BookingRequest


class BookingRequestForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.requires_client_details = not bool(user and user.is_authenticated)
        self.prefilled_identity = self.get_prefilled_identity()

        if self.requires_client_details:
            self.fields["phone"].required = True
            return

        for field_name in ("client_name", "email", "phone"):
            self.fields[field_name].required = False
            self.fields[field_name].widget = forms.HiddenInput()

    def get_prefilled_identity(self):
        user = self.user
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            return {
                "client_name": "",
                "email": "",
                "phone": "",
            }

        full_name = user.get_full_name().strip() if hasattr(user, "get_full_name") else ""
        latest_booking_phone = (
            BookingRequest.objects.filter(
                Q(client_account=user) | Q(email__iexact=user.email)
            )
            .exclude(phone="")
            .order_by("-created_at")
            .values_list("phone", flat=True)
            .first()
        )
        latest_payment_phone = (
            Payment.objects.filter(user=user)
            .exclude(phone_number="")
            .order_by("-paid_at", "-created_at")
            .values_list("phone_number", flat=True)
            .first()
        )
        return {
            "client_name": full_name or user.get_username(),
            "email": user.email,
            "phone": latest_booking_phone or latest_payment_phone or "",
        }

    def clean(self):
        cleaned_data = super().clean()

        if not self.requires_client_details:
            cleaned_data["client_name"] = self.prefilled_identity["client_name"]
            cleaned_data["email"] = self.prefilled_identity["email"]
            cleaned_data["phone"] = self.prefilled_identity["phone"]
            if not cleaned_data["email"]:
                self.add_error(
                    None,
                    "Add an email address to your account before booking from the client portal.",
                )

        return cleaned_data

    def save(self, commit=True):
        booking_request = super().save(commit=False)

        if self.user and self.user.is_authenticated:
            booking_request.client_account = self.user

        if commit:
            booking_request.save()

        return booking_request

    class Meta:
        model = BookingRequest
        fields = ("service", "client_name", "email", "phone", "event_date", "notes")
        widgets = {
            "service": forms.Select(
                attrs={
                    "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 focus:border-accent focus:outline-none",
                }
            ),
            "client_name": forms.TextInput(
                attrs={
                    "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                    "placeholder": "John Doe",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                    "placeholder": "john@example.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                    "placeholder": "+254 700 000 000",
                }
            ),
            "event_date": forms.DateInput(
                attrs={
                    "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 focus:border-accent focus:outline-none",
                    "type": "date",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "min-h-[160px] w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                    "placeholder": "Tell us about the event, creative direction, location, budget expectations, and anything else we should know.",
                }
            ),
        }
        labels = {
            "client_name": "Client name",
            "phone": "Phone number",
            "event_date": "Event/Project date",
            "notes": "Project notes",
        }
