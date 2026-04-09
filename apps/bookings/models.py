from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.text import slugify

from apps.projects.models import Project, ensure_client_upload_folder


class BookingRequest(models.Model):
    class Service(models.TextChoices):
        PHOTOGRAPHY = "Photography", "Photography"
        VIDEOGRAPHY = "Videography", "Videography"
        BRANDING = "Branding", "Branding"
        GRAPHIC_DESIGN = "Graphic Design", "Graphic Design"
        CLIENT_PORTAL_DEMO = "Client Portal Demo", "Client Portal Demo"

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUOTED = "quoted", "Quoted"
        CONFIRMED = "confirmed", "Confirmed"
        CONVERTED = "converted", "Converted"

    service = models.CharField(max_length=50, choices=Service.choices)
    client_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    event_date = models.DateField(verbose_name="Event/Project date")
    notes = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    client_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="booking_requests",
        blank=True,
        null=True,
    )
    converted_project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        related_name="booking_requests",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.client_name} - {self.service}"

    def clean(self):
        if self.status == self.Status.CONVERTED and not self.converted_project:
            raise ValidationError(
                {"status": "Converted bookings must be linked to a project."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @transaction.atomic
    def convert_to_project(self):
        if self.converted_project_id:
            if self.status != self.Status.CONVERTED:
                self.status = self.Status.CONVERTED
                self.save(update_fields=("status", "updated_at"))
            return self.converted_project

        if self.status != self.Status.CONFIRMED:
            raise ValidationError("Only confirmed bookings can be converted to projects.")

        client_account = self.get_or_create_client_account()
        project = Project.objects.create(
            client=client_account,
            title=self.build_project_title(),
            slug=self.build_unique_project_slug(client_account),
            service_type=self.service,
            status=Project.Status.PENDING,
            shoot_date=self.event_date,
            description=self.notes,
        )

        self.client_account = client_account
        self.converted_project = project
        self.status = self.Status.CONVERTED
        self.save(
            update_fields=(
                "client_account",
                "converted_project",
                "status",
                "updated_at",
            )
        )
        return project

    def get_or_create_client_account(self):
        if self.client_account_id:
            return self.client_account

        user_model = get_user_model()
        existing_user = user_model._default_manager.filter(email__iexact=self.email).first()
        if existing_user:
            ensure_client_upload_folder(existing_user)
            return existing_user

        username = self.build_unique_username(user_model)
        first_name, last_name = self.split_name()
        create_kwargs = {
            user_model.USERNAME_FIELD: username,
            "email": self.email,
        }
        if hasattr(user_model, "first_name"):
            create_kwargs["first_name"] = first_name
        if hasattr(user_model, "last_name"):
            create_kwargs["last_name"] = last_name

        user = user_model._default_manager.create_user(**create_kwargs)
        user.set_unusable_password()
        user.save()
        ensure_client_upload_folder(user)
        return user

    def build_project_title(self):
        return f"{self.service} - {self.client_name}"

    def build_unique_project_slug(self, client_account):
        base_slug = slugify(
            f"{self.service}-{self.client_name}-{self.event_date.isoformat()}"
        ) or f"booking-{self.pk or 'request'}"
        slug = base_slug
        suffix = 2

        while Project.objects.filter(client=client_account, slug=slug).exists():
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        return slug

    def build_unique_username(self, user_model):
        username_field = user_model.USERNAME_FIELD
        base_username = slugify(self.email.split("@", 1)[0]).replace("-", "_")
        if not base_username:
            base_username = slugify(self.client_name).replace("-", "_") or "client"

        username = base_username[:150]
        suffix = 2

        while user_model._default_manager.filter(**{username_field: username}).exists():
            trimmed = base_username[: max(1, 150 - len(str(suffix)) - 1)]
            username = f"{trimmed}_{suffix}"
            suffix += 1

        return username

    def split_name(self):
        parts = self.client_name.split(maxsplit=1)
        if len(parts) == 2:
            return parts[0], parts[1]
        if parts:
            return parts[0], ""
        return "", ""
