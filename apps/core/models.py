from django.db import models


class HeroCarousel(models.Model):
    class Section(models.TextChoices):
        HOME_MAIN = "home_main", "Homepage Main Hero"
        HOME_CTA = "home_cta", "Homepage Closing Hero"
        SERVICES_MAIN = "services_main", "Services Hero"
        SERVICES_EMPTY = "services_empty", "Services Empty Hero"
        PORTFOLIO_LIST = "portfolio_list", "Portfolio List Hero"
        PORTFOLIO_DETAIL = "portfolio_detail", "Portfolio Detail Hero"
        CONTACT_MAIN = "contact_main", "Contact Hero"

    section_key = models.CharField(
        max_length=40,
        choices=Section.choices,
        unique=True,
    )
    title = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional admin label. Defaults to the section name.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("section_key",)
        verbose_name = "Hero carousel"
        verbose_name_plural = "Hero carousels"

    def __str__(self):
        return self.title or self.get_section_key_display()

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self.get_section_key_display()
        super().save(*args, **kwargs)


class HeroCarouselSlide(models.Model):
    carousel = models.ForeignKey(
        HeroCarousel,
        on_delete=models.CASCADE,
        related_name="slides",
    )
    image = models.ImageField(upload_to="hero_carousels/%Y/%m/%d/")
    alt_text = models.CharField(max_length=160, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "id")
        verbose_name = "Hero carousel slide"
        verbose_name_plural = "Hero carousel slides"

    def __str__(self):
        label = self.alt_text or f"Slide {self.pk or ''}".strip()
        return f"{self.carousel} - {label}"


class HomeGalleryItem(models.Model):
    class Section(models.TextChoices):
        PHOTOGRAPHY = "photography", "Homepage Photography Gallery"
        VIDEOGRAPHY = "videography", "Homepage Videography Gallery"

    section = models.CharField(max_length=24, choices=Section.choices)
    title = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional admin label for easier recognition.",
    )
    image = models.ImageField(upload_to="home_gallery/%Y/%m/%d/")
    alt_text = models.CharField(max_length=160, blank=True)
    project_slug = models.CharField(
        max_length=80,
        blank=True,
        help_text="Optional portfolio project slug to open when this image is clicked.",
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("section", "display_order", "id")
        verbose_name = "Homepage gallery item"
        verbose_name_plural = "Homepage gallery items"

    def __str__(self):
        return self.title or self.alt_text or self.get_section_display()
