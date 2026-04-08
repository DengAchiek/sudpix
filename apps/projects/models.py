from urllib.parse import urlencode

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Project(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_REVIEW = "in_review", "In Review"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        COMPLETED = "completed", "Completed"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    service_type = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    shoot_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    cover_image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-shoot_date", "-updated_at", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("client", "slug"),
                name="unique_client_project_slug",
            )
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{reverse('client:files')}?{urlencode({'project': self.slug})}"

    @property
    def status_badge_class(self):
        return {
            self.Status.READY: "bg-green-500/15 text-green-300",
            self.Status.COMPLETED: "bg-emerald-500/15 text-emerald-300",
            self.Status.IN_REVIEW: "bg-amber-500/15 text-amber-300",
            self.Status.PROCESSING: "bg-blue-500/15 text-blue-300",
            self.Status.PENDING: "bg-white/10 text-soft/80",
        }.get(self.status, "bg-white/10 text-soft/80")

    @property
    def cover_url(self):
        default_covers = {
            "photography": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=80",
            "videography": "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=1200&q=80",
            "branding": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
            "graphic design": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1200&q=80",
        }
        return self.cover_image_url or default_covers.get(
            self.service_type.lower(),
            default_covers["photography"],
        )


def build_client_upload_folder_title(client):
    full_name = client.get_full_name().strip() if hasattr(client, "get_full_name") else ""
    return f"{full_name or client.get_username()} Files"


def build_client_upload_folder_slug(client):
    base_slug = slugify(f"{client.get_username()}-files")
    if base_slug:
        return base_slug
    return f"client-{client.pk}-files"


def ensure_client_upload_folder(client):
    project, created = Project.objects.get_or_create(
        client=client,
        slug=build_client_upload_folder_slug(client),
        defaults={
            "title": build_client_upload_folder_title(client),
            "service_type": "Client Files",
            "status": Project.Status.READY,
            "description": "Auto-created folder for client uploads.",
        },
    )

    if not created and not project.title:
        project.title = build_client_upload_folder_title(client)
        project.save(update_fields=("title", "updated_at"))

    return project
