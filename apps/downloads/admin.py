from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Download


@admin.action(description="Mark selected downloads as ready")
def mark_as_ready(modeladmin, request, queryset):
    count = queryset.update(status=Download.Status.READY, available_at=timezone.now())
    modeladmin.message_user(request, f"{count} download(s) marked as ready.")


@admin.action(description="Lock selected downloads")
def mark_as_locked(modeladmin, request, queryset):
    count = queryset.update(status=Download.Status.LOCKED, available_at=None)
    modeladmin.message_user(request, f"{count} download(s) locked.")


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    actions = (mark_as_ready, mark_as_locked)
    fields = (
        "user",
        "project",
        "payment",
        "title",
        "description",
        "status",
        "file",
        "file_url",
        "file_link",
        "available_at",
    )
    list_display = ("title", "user", "project", "status", "has_uploaded_file", "available_at")
    list_select_related = ("user", "project", "payment")
    list_filter = ("status",)
    readonly_fields = ("file_link",)
    search_fields = ("title", "user__username", "project__title")

    @admin.display(boolean=True, description="Uploaded")
    def has_uploaded_file(self, obj):
        return bool(obj.file)

    @admin.display(description="Download file")
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Open uploaded download</a>', obj.file.url)
        if obj.file_url:
            return format_html('<a href="{}" target="_blank">Open external download</a>', obj.file_url)
        return "-"
