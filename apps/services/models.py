from django.db import models
from django.utils.text import slugify


class Service(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    badge = models.CharField(max_length=160)
    heading = models.CharField(max_length=255)
    description = models.TextField()
    included_items = models.TextField(
        help_text="One included item per line.",
        blank=True,
    )
    best_for_items = models.TextField(
        help_text="One best-fit use case per line.",
        blank=True,
    )
    packages_heading = models.CharField(max_length=160)
    book_label = models.CharField(max_length=160)
    booking_service = models.CharField(max_length=120)
    teaser = models.CharField(max_length=255)
    icon = models.CharField(max_length=16, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.badge:
            self.badge = f"{self.name} Services"
        if not self.packages_heading:
            self.packages_heading = f"{self.name} Packages"
        if not self.book_label:
            self.book_label = f"Book {self.name}"
        if not self.booking_service:
            self.booking_service = self.name
        super().save(*args, **kwargs)

    @staticmethod
    def _split_lines(value):
        return [line.strip() for line in value.splitlines() if line.strip()]

    @property
    def included_list(self):
        return self._split_lines(self.included_items)

    @property
    def best_for_list(self):
        return self._split_lines(self.best_for_items)


class ServicePackage(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="packages",
    )
    name = models.CharField(max_length=160)
    price_label = models.CharField(
        max_length=80,
        help_text="Examples: KES 12,000 or Custom Quote",
    )
    description = models.TextField()
    highlighted = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "id")

    def __str__(self):
        return f"{self.service.name} - {self.name}"
