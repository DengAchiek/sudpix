from django.conf import settings
from django.db import models


class AdminNotification(models.Model):
    class Kind(models.TextChoices):
        CLIENT_REGISTERED = "client_registered", "Client registered"
        BOOKING_REQUESTED = "booking_requested", "Booking requested"

    kind = models.CharField(max_length=50, choices=Kind.choices)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="admin_notifications",
        blank=True,
        null=True,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("is_read", "-created_at")

    def __str__(self):
        return self.title


def create_client_registration_notification(user):
    full_name = user.get_full_name().strip() if hasattr(user, "get_full_name") else ""
    display_name = full_name or user.get_username()
    return AdminNotification.objects.create(
        kind=AdminNotification.Kind.CLIENT_REGISTERED,
        title="New client registration",
        message=f"{display_name} just created a SudPix client account.",
        related_user=user,
    )


def create_booking_request_notification(booking_request):
    signed_in_label = (
        booking_request.client_account.get_username()
        if booking_request.client_account_id
        else "Guest client"
    )
    return AdminNotification.objects.create(
        kind=AdminNotification.Kind.BOOKING_REQUESTED,
        title="New service booking",
        message=(
            f"{booking_request.client_name} submitted a {booking_request.service} booking "
            f"for {booking_request.event_date}. Account: {signed_in_label}."
        ),
        related_user=booking_request.client_account,
    )
