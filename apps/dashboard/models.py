from django.conf import settings
from django.db import models


class DownloadEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="download_events",
    )
    media_asset = models.ForeignKey(
        "media_management.MediaAsset",
        on_delete=models.CASCADE,
        related_name="download_events",
    )
    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.SET_NULL,
        related_name="download_events",
        blank=True,
        null=True,
    )
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-downloaded_at",)

    def __str__(self):
        return f"{self.user} downloaded {self.media_asset}"
