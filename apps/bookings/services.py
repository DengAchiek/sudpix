import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import BookingRequest

logger = logging.getLogger(__name__)

PROGRESS_COPY = {
    BookingRequest.Status.NEW: {
        "subject": "We received your SudPix booking request",
        "headline": "Your booking request is in the SudPix queue.",
        "message": "Our team will review your brief and contact you with the next production step.",
    },
    BookingRequest.Status.CONTACTED: {
        "subject": "SudPix has started your booking review",
        "headline": "We have started reviewing your project details.",
        "message": "A SudPix team member will use your booking notes to confirm scope, timing, and any missing details.",
    },
    BookingRequest.Status.QUOTED: {
        "subject": "Your SudPix booking has been quoted",
        "headline": "Your project is ready for quote review.",
        "message": "Review the quote details from the SudPix team so we can lock the schedule and prepare your workspace.",
    },
    BookingRequest.Status.CONFIRMED: {
        "subject": "Your SudPix booking is confirmed",
        "headline": "Your booking is confirmed.",
        "message": "We will prepare your client workspace so you can follow the brief, timeline, media review, approvals, payments, and final delivery.",
    },
}


def send_booking_progress_notification(booking_request, *, force=False):
    copy = PROGRESS_COPY.get(booking_request.status)
    if copy is None or not booking_request.email:
        return False
    if (
        not force
        and booking_request.last_progress_notified_status == booking_request.status
    ):
        return False

    login_url = build_absolute_url(reverse("accounts:client_login"))
    context = {
        "booking": booking_request,
        "headline": copy["headline"],
        "message": copy["message"],
        "login_url": login_url,
        "site_url": get_site_url(),
    }
    sent = send_templated_mail(
        subject=copy["subject"],
        template_name="bookings/emails/progress_notification.txt",
        context=context,
        recipients=[booking_request.email],
    )
    if sent:
        booking_request.mark_progress_notified()
    return sent


def send_booking_portal_invite(booking_request, *, force=False):
    if (
        not booking_request.email
        or not booking_request.client_account_id
        or not booking_request.converted_project_id
    ):
        return False
    if booking_request.portal_invite_sent_at and not force:
        return False

    user = booking_request.client_account
    project = booking_request.converted_project
    project_url = build_absolute_url(project.get_absolute_url())
    login_url = build_absolute_url(reverse("accounts:client_login"))
    activation_url = ""

    if not user.has_usable_password():
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_url = build_absolute_url(
            reverse("accounts:password_reset_confirm", args=[uid, token])
        )

    context = {
        "booking": booking_request,
        "user": user,
        "project": project,
        "project_url": project_url,
        "login_url": login_url,
        "activation_url": activation_url,
        "site_url": get_site_url(),
    }
    sent = send_templated_mail(
        subject=f"Your SudPix workspace is ready: {project.title}",
        template_name="bookings/emails/portal_invite.txt",
        context=context,
        recipients=[booking_request.email],
    )
    if sent:
        booking_request.mark_portal_invite_sent()
    return sent


def send_templated_mail(*, subject, template_name, context, recipients):
    message = render_to_string(template_name, context).strip()
    try:
        return send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send booking email '%s' to %s", subject, recipients)
        return 0


def get_site_url():
    site_url = getattr(settings, "SUDPIX_SITE_URL", "").strip().rstrip("/")
    return site_url or "https://sudpix.com"


def build_absolute_url(path):
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{get_site_url()}{path}"
