from django.contrib import admin
from django.utils import timezone

from apps.downloads.models import Download
from .models import Payment
from .services import lock_downloads_for_payment, unlock_downloads_for_payment


@admin.action(description="Mark selected payments as confirmed")
def mark_as_confirmed(modeladmin, request, queryset):
    timestamp = timezone.now()
    payments = list(queryset)
    for payment in payments:
        payment.status = Payment.Status.CONFIRMED
        payment.paid_at = timestamp
        payment.save(update_fields=("status", "paid_at"))
        unlock_downloads_for_payment(payment)
    count = len(payments)
    modeladmin.message_user(request, f"{count} payment(s) marked as confirmed.")


@admin.action(description="Mark selected payments as pending")
def mark_as_pending(modeladmin, request, queryset):
    payments = list(queryset)
    for payment in payments:
        payment.status = Payment.Status.PENDING
        payment.paid_at = None
        payment.save(update_fields=("status", "paid_at"))
        lock_downloads_for_payment(payment, download_status=Download.Status.PROCESSING)
    count = len(payments)
    modeladmin.message_user(request, f"{count} payment(s) moved back to pending.")


@admin.action(description="Mark selected payments as failed")
def mark_as_failed(modeladmin, request, queryset):
    payments = list(queryset)
    for payment in payments:
        payment.status = Payment.Status.FAILED
        payment.paid_at = None
        payment.save(update_fields=("status", "paid_at"))
        lock_downloads_for_payment(payment)
    count = len(payments)
    modeladmin.message_user(request, f"{count} payment(s) marked as failed.")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    actions = (mark_as_confirmed, mark_as_pending, mark_as_failed)
    list_display = (
        "user",
        "project_label",
        "selected_file_count",
        "method",
        "amount",
        "status",
        "checkout_request_id",
        "created_at",
    )
    list_filter = ("method", "status")
    list_select_related = ("user", "project")
    search_fields = (
        "user__username",
        "project__title",
        "reference",
        "merchant_request_id",
        "checkout_request_id",
        "phone_number",
    )
