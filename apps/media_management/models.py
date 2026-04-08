from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from django.db import models

from apps.core.utils import format_currency


class MediaAsset(models.Model):
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
    DEFAULT_PRICES = {
        "photo": Decimal("80.00"),
        "video": Decimal("500.00"),
    }

    class Kind(models.TextChoices):
        PHOTO = "photo", "Photo"
        VIDEO = "video", "Video"
        DESIGN = "design", "Design"
        DOCUMENT = "document", "Document"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="media_files",
    )
    title = models.CharField(max_length=255)
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.PHOTO,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preview_image = models.ImageField(
        upload_to="previews/%Y/%m/%d/",
        blank=True,
    )
    preview_image_url = models.URLField(blank=True)
    file = models.FileField(
        upload_to="project_assets/%Y/%m/%d/",
        blank=True,
    )
    file_url = models.URLField(blank=True)
    is_highlight = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-uploaded_at", "title")

    def __str__(self):
        return f"{self.project.title} - {self.title}"

    def save(self, *args, **kwargs):
        if self.kind in self.DEFAULT_PRICES and Decimal(self.price or 0) <= 0:
            self.price = self.default_price_for_kind(self.kind)
        super().save(*args, **kwargs)

    @classmethod
    def default_price_for_kind(cls, kind):
        return cls.DEFAULT_PRICES.get(kind, Decimal("0"))

    @property
    def client_price(self):
        default_price = self.default_price_for_kind(self.kind)
        if default_price > 0:
            return default_price
        return Decimal(self.price or 0)

    @property
    def formatted_price(self):
        return format_currency(self.client_price)

    @property
    def preview_url(self):
        default_previews = {
            self.Kind.PHOTO: "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=900&q=80",
            self.Kind.VIDEO: "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=900&q=80",
            self.Kind.DESIGN: "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=900&q=80",
            self.Kind.DOCUMENT: "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80",
        }
        if self.preview_image:
            return self.preview_image.url
        if self.is_previewable_image and self.file:
            return self.file.url
        return self.preview_image_url or default_previews[self.kind]

    @property
    def asset_url(self):
        if self.file:
            return self.file.url
        return self.file_url

    @property
    def is_previewable_image(self):
        if not self.file:
            return False
        return Path(self.file.name).suffix.lower() in self.IMAGE_EXTENSIONS

    @property
    def has_downloadable_file(self):
        return bool(self.asset_url)

    @property
    def download_name(self):
        if self.file:
            return Path(self.file.name).name
        if self.file_url:
            remote_name = Path(urlparse(self.file_url).path).name
            if remote_name:
                return remote_name
        return self.title
