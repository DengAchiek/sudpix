from django.conf import settings
from django.db import models


class Download(models.Model):
    class Status(models.TextChoices):
        LOCKED = "locked", "Locked"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="downloads",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="downloads",
    )
    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.SET_NULL,
        related_name="downloads",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LOCKED)
    file = models.FileField(
        upload_to="downloads/%Y/%m/%d/",
        blank=True,
    )
    file_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    available_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-available_at", "-created_at")

    def __str__(self):
        return self.title

    @property
    def status_badge_class(self):
        return {
            self.Status.READY: "bg-green-500/15 text-green-300",
            self.Status.PROCESSING: "bg-blue-500/15 text-blue-300",
            self.Status.LOCKED: "bg-white/10 text-soft/80",
        }.get(self.status, "bg-white/10 text-soft/80")

    @property
    def is_ready(self):
        return self.status == self.Status.READY

    @property
    def download_url(self):
        if self.file:
            return self.file.url
        return self.file_url
