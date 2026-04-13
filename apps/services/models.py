from django.db import models
from django.utils.text import slugify


class Service(models.Model):
    SHOWCASE_MEDIA = {
        "photography": {
            "type": "image",
            "url": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1400&q=80",
            "eyebrow": "Signature Frames",
            "title": "Clean compositions, premium lighting, and story-led image delivery",
            "description": "SudPix photography blends event emotion with polished editorial direction so the final gallery feels both premium and personal.",
            "stats": [
                {"label": "Sample Sets", "value": "Portraits"},
                {"label": "Coverage", "value": "Events"},
                {"label": "Delivery", "value": "Albums"},
            ],
            "samples": [
                {
                    "label": "Wedding",
                    "url": "https://images.unsplash.com/photo-1511285560929-80b456fea0bc?auto=format&fit=crop&w=900&q=80",
                },
                {
                    "label": "Portrait",
                    "url": "https://images.unsplash.com/photo-1504593811423-6dd665756598?auto=format&fit=crop&w=900&q=80",
                },
                {
                    "label": "Lifestyle",
                    "url": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80",
                },
                {
                    "label": "Product",
                    "url": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=900&q=80",
                },
            ],
        },
        "videography": {
            "type": "video",
            "url": "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
            "poster": "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=1400&q=80",
            "eyebrow": "Motion Preview",
            "title": "A live video clip preview for cinematic event coverage and branded storytelling",
            "description": "The videography experience now opens with motion, giving visitors an immediate feel for pacing, atmosphere, and the premium SudPix finish.",
        },
        "branding": {
            "type": "image",
            "url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1400&q=80",
            "eyebrow": "Brand Direction",
            "title": "Identity systems designed to look premium across launch, web, and campaign assets",
            "description": "From executive decks to social rollouts, SudPix branding work is structured for consistency, confidence, and stronger market presence.",
        },
        "graphic-design": {
            "type": "image",
            "url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1400&q=80",
            "eyebrow": "Design Showcase",
            "title": "Campaign-ready graphics that stay bold, clear, and conversion-focused",
            "description": "SudPix design output balances visual impact with clean hierarchy so marketing graphics feel premium without losing clarity.",
        },
    }

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

    @property
    def showcase_media(self):
        default_media = {
            "type": "image",
            "url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1400&q=80",
            "eyebrow": "SudPix Showcase",
            "title": "Premium creative direction built around clear stories and polished delivery",
            "description": "Every SudPix service is presented with premium visual treatment to match the quality of the final work clients receive.",
            "stats": [],
            "samples": [],
        }
        return {
            **default_media,
            **self.SHOWCASE_MEDIA.get(self.slug, {}),
        }


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
