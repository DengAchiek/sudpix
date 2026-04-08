from django.contrib import admin

from .models import DownloadEvent


@admin.register(DownloadEvent)
class DownloadEventAdmin(admin.ModelAdmin):
    list_display = ("user", "media_asset", "payment", "downloaded_at")
    list_select_related = ("user", "media_asset__project", "payment")
    search_fields = (
        "user__username",
        "user__email",
        "media_asset__title",
        "media_asset__project__title",
        "payment__reference",
    )
