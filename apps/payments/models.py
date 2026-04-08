from django.conf import settings
from django.db import models

from apps.core.utils import format_currency


class Payment(models.Model):
    class Method(models.TextChoices):
        MPESA = "mpesa", "M-Pesa"
        CARD = "card", "Card"
        MOBILE_MONEY = "mobile_money", "Mobile Money"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        related_name="payments",
        blank=True,
        null=True,
    )
    media_assets = models.ManyToManyField(
        "media_management.MediaAsset",
        blank=True,
        related_name="payments",
    )
    merchant_request_id = models.CharField(max_length=128, blank=True)
    checkout_request_id = models.CharField(max_length=128, blank=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.MPESA)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    phone_number = models.CharField(max_length=32, blank=True)
    reference = models.CharField(max_length=64, blank=True)
    gateway_response_code = models.CharField(max_length=32, blank=True)
    gateway_response_message = models.TextField(blank=True)
    result_code = models.IntegerField(blank=True, null=True)
    result_desc = models.TextField(blank=True)
    raw_response = models.JSONField(blank=True, default=dict)
    prompt_sent_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-paid_at", "-created_at")

    def __str__(self):
        return f"{self.get_method_display()} - {self.formatted_amount}"

    @property
    def formatted_amount(self):
        return format_currency(self.amount)

    @property
    def project_label(self):
        if self.project:
            return self.project.title
        selected_assets = list(self.media_assets.all())
        project_titles = sorted({asset.project.title for asset in selected_assets})
        if len(project_titles) == 1:
            return project_titles[0]
        if project_titles:
            return "Multiple folders"
        return "Multiple folders"

    @property
    def selected_file_count(self):
        selected_count = len(self.media_assets.all())
        if selected_count:
            return selected_count
        if self.project_id:
            return self.project.media_files.filter(kind__in=("photo", "video")).count()
        return 0

    @property
    def selected_file_label(self):
        count = self.selected_file_count
        return f"{count} file" if count == 1 else f"{count} files"

    @property
    def status_badge_class(self):
        return {
            self.Status.CONFIRMED: "bg-green-500/15 text-green-300",
            self.Status.PENDING: "bg-amber-500/15 text-amber-300",
            self.Status.FAILED: "bg-red-500/15 text-red-300",
        }.get(self.status, "bg-white/10 text-soft/80")
