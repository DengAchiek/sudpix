from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
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
        return reverse("client:project_detail", args=[self.slug])

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


class ProjectBrief(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="brief",
    )
    objective = models.TextField()
    audience = models.CharField(max_length=255, blank=True)
    deliverables = models.TextField()
    creative_direction = models.TextField(blank=True)
    reference_links = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "project brief"
        verbose_name_plural = "project briefs"

    def __str__(self):
        return f"Brief - {self.project.title}"


class ProjectMilestone(models.Model):
    class Status(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        ACTIVE = "active", "In progress"
        COMPLETED = "completed", "Completed"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="milestones",
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)
    due_date = models.DateField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "due_date", "id")

    def __str__(self):
        return f"{self.project.title} - {self.title}"

    @property
    def status_badge_class(self):
        return {
            self.Status.COMPLETED: "border-green-400/25 bg-green-500/10 text-green-300",
            self.Status.ACTIVE: "border-gold/30 bg-gold/10 text-gold",
            self.Status.UPCOMING: "border-white/10 bg-white/5 text-soft/70",
        }[self.status]


class ProjectFeedback(models.Model):
    class Area(models.TextChoices):
        BRIEF = "brief", "Brief"
        GALLERY = "gallery", "Gallery"
        DELIVERY = "delivery", "Delivery"
        GENERAL = "general", "General"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="feedback_entries",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_feedback_entries",
    )
    area = models.CharField(max_length=20, choices=Area.choices, default=Area.GENERAL)
    message = models.TextField()
    studio_reply = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = "project feedback"

    def __str__(self):
        return f"{self.project.title} feedback by {self.author}"


class RevisionRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        IN_PROGRESS = "in_progress", "In progress"
        READY_FOR_REVIEW = "ready_for_review", "Ready for review"
        RESOLVED = "resolved", "Resolved"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="revision_requests",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="revision_requests",
    )
    media_asset = models.ForeignKey(
        "media_management.MediaAsset",
        on_delete=models.SET_NULL,
        related_name="revision_requests",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=160)
    details = models.TextField()
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.REQUESTED)
    studio_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.project.title} - {self.title}"

    @property
    def status_badge_class(self):
        return {
            self.Status.REQUESTED: "border-amber-400/25 bg-amber-500/10 text-amber-200",
            self.Status.IN_PROGRESS: "border-blue-400/25 bg-blue-500/10 text-blue-200",
            self.Status.READY_FOR_REVIEW: "border-gold/30 bg-gold/10 text-gold",
            self.Status.RESOLVED: "border-green-400/25 bg-green-500/10 text-green-300",
        }[self.status]


class ProjectApproval(models.Model):
    class Decision(models.TextChoices):
        PENDING = "pending", "Awaiting approval"
        APPROVED = "approved", "Approved"
        REVISIONS_REQUESTED = "revisions_requested", "Revisions requested"

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="approval",
    )
    decision = models.CharField(max_length=24, choices=Decision.choices, default=Decision.PENDING)
    note = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="project_approvals",
        blank=True,
        null=True,
    )
    decided_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.title} - {self.get_decision_display()}"

    @property
    def status_badge_class(self):
        return {
            self.Decision.PENDING: "border-white/10 bg-white/5 text-soft/70",
            self.Decision.APPROVED: "border-green-400/25 bg-green-500/10 text-green-300",
            self.Decision.REVISIONS_REQUESTED: "border-amber-400/25 bg-amber-500/10 text-amber-200",
        }[self.decision]

    def approve(self, user, note=""):
        self.decision = self.Decision.APPROVED
        self.note = note
        self.decided_by = user
        self.decided_at = timezone.now()


class FinalDelivery(models.Model):
    class Status(models.TextChoices):
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready for approval"
        RELEASED = "released", "Released"

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="final_delivery",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PREPARING)
    summary = models.TextField(blank=True)
    release_note = models.TextField(blank=True)
    released_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "final deliveries"

    def __str__(self):
        return f"Delivery - {self.project.title}"

    @property
    def status_badge_class(self):
        return {
            self.Status.PREPARING: "border-white/10 bg-white/5 text-soft/70",
            self.Status.READY: "border-gold/30 bg-gold/10 text-gold",
            self.Status.RELEASED: "border-green-400/25 bg-green-500/10 text-green-300",
        }[self.status]


def initialize_project_workspace(project):
    ProjectBrief.objects.get_or_create(
        project=project,
        defaults={
            "objective": project.description or "Confirm the creative objective with the SudPix team.",
            "deliverables": f"{project.service_type or 'Creative'} deliverables to be confirmed.",
        },
    )
    milestone_titles = (
        "Brief received",
        "Date confirmed",
        "Shoot completed",
        "Gallery uploaded",
        "Client selections made",
        "Payment completed",
        "Final downloads unlocked",
    )
    for display_order, title in enumerate(milestone_titles, start=1):
        completed = display_order <= 2 and bool(project.shoot_date)
        ProjectMilestone.objects.get_or_create(
            project=project,
            title=title,
            defaults={
                "display_order": display_order,
                "status": (
                    ProjectMilestone.Status.COMPLETED
                    if completed
                    else ProjectMilestone.Status.UPCOMING
                ),
                "completed_at": timezone.now() if completed else None,
            },
        )
    ProjectApproval.objects.get_or_create(project=project)
    FinalDelivery.objects.get_or_create(
        project=project,
        defaults={
            "summary": "Final files will appear here after review and payment confirmation.",
        },
    )


def ensure_project_workspace(project):
    if not project.milestones.exists():
        initialize_project_workspace(project)
        return

    ProjectBrief.objects.get_or_create(
        project=project,
        defaults={
            "objective": project.description or "Confirm the creative objective with the SudPix team.",
            "deliverables": f"{project.service_type or 'Creative'} deliverables to be confirmed.",
        },
    )
    ProjectApproval.objects.get_or_create(project=project)
    FinalDelivery.objects.get_or_create(
        project=project,
        defaults={
            "summary": "Final files will appear here after review and payment confirmation.",
        },
    )


def complete_project_milestone(project, title):
    ensure_project_workspace(project)
    ProjectMilestone.objects.filter(
        project=project,
        title=title,
    ).exclude(status=ProjectMilestone.Status.COMPLETED).update(
        status=ProjectMilestone.Status.COMPLETED,
        completed_at=timezone.now(),
    )


def release_final_delivery(project):
    ensure_project_workspace(project)
    delivery, _ = FinalDelivery.objects.get_or_create(project=project)
    delivery.status = FinalDelivery.Status.RELEASED
    delivery.release_note = "Payment confirmed. Final files are unlocked for secure download."
    delivery.released_at = timezone.now()
    delivery.save(update_fields=("status", "release_note", "released_at", "updated_at"))


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
