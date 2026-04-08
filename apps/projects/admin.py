from django.contrib import admin
from django.db.models import Count

from apps.downloads.models import Download
from apps.media_management.models import MediaAsset
from apps.payments.models import Payment
from .models import Project


class MediaAssetInline(admin.TabularInline):
    model = MediaAsset
    extra = 0
    fields = (
        "title",
        "kind",
        "price",
        "preview_image",
        "preview_image_url",
        "file",
        "file_url",
        "is_highlight",
        "is_edited",
        "uploaded_at",
    )
    readonly_fields = ("uploaded_at",)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("user", "amount", "method", "status", "reference", "created_at")
    readonly_fields = ("created_at",)


class DownloadInline(admin.TabularInline):
    model = Download
    extra = 0
    fields = ("user", "title", "status", "file", "file_url", "available_at")
    readonly_fields = ("available_at",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = (MediaAssetInline, PaymentInline, DownloadInline)
    list_display = (
        "title",
        "client",
        "service_type",
        "status",
        "shoot_date",
        "files_total",
        "payments_total",
        "downloads_total",
    )
    list_filter = ("status", "service_type")
    list_select_related = ("client",)
    search_fields = ("title", "client__username", "client__email")
    prepopulated_fields = {"slug": ("title",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            files_total_value=Count("media_files", distinct=True),
            payments_total_value=Count("payments", distinct=True),
            downloads_total_value=Count("downloads", distinct=True),
        )

    @admin.display(ordering="files_total_value", description="Files")
    def files_total(self, obj):
        return obj.files_total_value

    @admin.display(ordering="payments_total_value", description="Payments")
    def payments_total(self, obj):
        return obj.payments_total_value

    @admin.display(ordering="downloads_total_value", description="Downloads")
    def downloads_total(self, obj):
        return obj.downloads_total_value
