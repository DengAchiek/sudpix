from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html

from .models import BookingRequest


@admin.action(description="Mark selected bookings as contacted")
def mark_as_contacted(modeladmin, request, queryset):
    count = queryset.update(status=BookingRequest.Status.CONTACTED)
    modeladmin.message_user(request, f"{count} booking(s) marked as contacted.")


@admin.action(description="Mark selected bookings as quoted")
def mark_as_quoted(modeladmin, request, queryset):
    count = queryset.update(status=BookingRequest.Status.QUOTED)
    modeladmin.message_user(request, f"{count} booking(s) marked as quoted.")


@admin.action(description="Mark selected bookings as confirmed")
def mark_as_confirmed(modeladmin, request, queryset):
    count = queryset.update(status=BookingRequest.Status.CONFIRMED)
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


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    actions = (
        mark_as_contacted,
        mark_as_quoted,
        mark_as_confirmed,
        convert_confirmed_bookings,
    )
    list_display = (
        "client_name",
        "service",
        "event_date",
        "status",
        "client_account_link",
        "project_link",
        "created_at",
    )
    list_filter = ("status", "service", "event_date")
    list_select_related = ("client_account", "converted_project")
    readonly_fields = ("client_account", "converted_project", "created_at", "updated_at")
    search_fields = ("client_name", "email", "phone")

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
