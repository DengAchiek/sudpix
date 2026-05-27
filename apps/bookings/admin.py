from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html

from .models import BookingRequest


@admin.action(description="Mark selected bookings as contacted")
def mark_as_contacted(modeladmin, request, queryset):
    count = transition_bookings(queryset, BookingRequest.Status.CONTACTED)
    modeladmin.message_user(request, f"{count} booking(s) marked as contacted.")


@admin.action(description="Mark selected bookings as quoted")
def mark_as_quoted(modeladmin, request, queryset):
    count = transition_bookings(queryset, BookingRequest.Status.QUOTED)
    modeladmin.message_user(request, f"{count} booking(s) marked as quoted.")


@admin.action(description="Mark selected bookings as confirmed")
def mark_as_confirmed(modeladmin, request, queryset):
    count = transition_bookings(queryset, BookingRequest.Status.CONFIRMED)
    modeladmin.message_user(request, f"{count} booking(s) marked as confirmed.")


@admin.action(description="Convert confirmed bookings to projects")
def convert_confirmed_bookings(modeladmin, request, queryset):
    converted = 0
    skipped = 0

    for booking_request in queryset:
        try:
            booking_request.convert_to_project()
            converted += 1
        except ValidationError:
            skipped += 1

    if converted:
        modeladmin.message_user(
            request,
            f"{converted} booking(s) converted to projects.",
            level=messages.SUCCESS,
        )
    if skipped:
        modeladmin.message_user(
            request,
            f"{skipped} booking(s) were skipped because they are not confirmed yet.",
            level=messages.WARNING,
        )


@admin.action(description="Resend portal invites for converted bookings")
def resend_portal_invites(modeladmin, request, queryset):
    sent = 0
    skipped = 0

    for booking_request in queryset.select_related("client_account", "converted_project"):
        if booking_request.send_portal_invite(force=True):
            sent += 1
        else:
            skipped += 1

    if sent:
        modeladmin.message_user(request, f"{sent} portal invite(s) resent.", level=messages.SUCCESS)
    if skipped:
        modeladmin.message_user(
            request,
            f"{skipped} booking(s) did not have a converted project or email address.",
            level=messages.WARNING,
        )


def transition_bookings(queryset, status):
    changed = 0
    for booking_request in queryset:
        if booking_request.transition_to_status(status):
            changed += 1
    return changed


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    actions = (
        mark_as_contacted,
        mark_as_quoted,
        mark_as_confirmed,
        convert_confirmed_bookings,
        resend_portal_invites,
    )
    list_display = (
        "client_name",
        "service",
        "event_date",
        "status",
        "progress_notified",
        "portal_invited",
        "client_account_link",
        "project_link",
        "created_at",
    )
    list_filter = ("status", "service", "event_date")
    list_select_related = ("client_account", "converted_project")
    readonly_fields = (
        "client_account",
        "converted_project",
        "portal_invite_sent_at",
        "last_progress_notified_status",
        "progress_notified_at",
        "created_at",
        "updated_at",
    )
    search_fields = ("client_name", "email", "phone")

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change and obj.pk:
            previous_status = (
                BookingRequest.objects.filter(pk=obj.pk)
                .values_list("status", flat=True)
                .first()
            )

        super().save_model(request, obj, form, change)

        if previous_status and previous_status != obj.status:
            obj.send_progress_notification()

    @admin.display(description="Client account")
    def client_account_link(self, obj):
        if not obj.client_account_id:
            return "-"

        url = reverse("admin:auth_user_change", args=[obj.client_account_id])
        return format_html('<a href="{}">{}</a>', url, obj.client_account.username)

    @admin.display(description="Converted project")
    def project_link(self, obj):
        if not obj.converted_project_id:
            return "-"

        url = reverse("admin:projects_project_change", args=[obj.converted_project_id])
        return format_html('<a href="{}">{}</a>', url, obj.converted_project.title)

    @admin.display(boolean=True, description="Progress email")
    def progress_notified(self, obj):
        return bool(obj.progress_notified_at)

    @admin.display(boolean=True, description="Portal invite")
    def portal_invited(self, obj):
        return bool(obj.portal_invite_sent_at)
