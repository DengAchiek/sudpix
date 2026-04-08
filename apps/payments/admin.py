from django.contrib import admin
from django.utils import timezone

from apps.downloads.models import Download
from .models import Payment


@admin.action(description="Mark selected payments as confirmed")
def mark_as_confirmed(modeladmin, request, queryset):
    timestamp = timezone.now()
    count = queryset.update(status=Payment.Status.CONFIRMED, paid_at=timestamp)
    Download.objects.filter(payment__in=queryset).update(
        status=Download.Status.READY,
        available_at=timestamp,
    )
    modeladmin.message_user(request, f"{count} payment(s) marked as confirmed.")


@admin.action(description="Mark selected payments as pending")
def mark_as_pending(modeladmin, request, queryset):
    count = queryset.update(status=Payment.Status.PENDING, paid_at=None)
    Download.objects.filter(payment__in=queryset).update(
        status=Download.Status.PROCESSING,
        available_at=None,
    )
    modeladmin.message_user(request, f"{count} payment(s) moved back to pending.")


@admin.action(description="Mark selected payments as failed")
def mark_as_failed(modeladmin, request, queryset):
    count = queryset.update(status=Payment.Status.FAILED, paid_at=None)
    Download.objects.filter(payment__in=queryset).update(
        status=Download.Status.LOCKED,
        available_at=None,
    )
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
