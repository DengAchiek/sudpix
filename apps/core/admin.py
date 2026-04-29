from django.contrib import admin
from django.utils.html import format_html

from .models import HeroCarousel, HeroCarouselSlide


class HeroCarouselSlideInline(admin.TabularInline):
    model = HeroCarouselSlide
    extra = 1
    fields = ("display_order", "image", "alt_text", "preview")
    readonly_fields = ("preview",)
    ordering = ("display_order", "id")

    @admin.display(description="Preview")
    def preview(self, obj):
        if not obj.pk or not obj.image:
            return "Upload an image"
        return format_html(
            '<img src="{}" alt="{}" style="height: 72px; width: 128px; object-fit: cover; border-radius: 8px;" />',
            obj.image.url,
            obj.alt_text or obj.carousel,
        )


@admin.register(HeroCarousel)
class HeroCarouselAdmin(admin.ModelAdmin):
    inlines = (HeroCarouselSlideInline,)
    list_display = ("title", "section_key", "is_active", "slides_total", "updated_at")
    list_filter = ("section_key", "is_active")
    search_fields = ("title", "section_key")
    list_editable = ("is_active",)

    fieldsets = (
        (
            "Carousel setup",
            {
                "fields": (
                    "section_key",
                    "title",
                    "is_active",
                )
            },
        ),
    )

    @admin.display(description="Slides")
    def slides_total(self, obj):
        return obj.slides.count()


@admin.register(HeroCarouselSlide)
class HeroCarouselSlideAdmin(admin.ModelAdmin):
    list_display = ("carousel", "display_order", "alt_text", "preview")
    list_filter = ("carousel__section_key",)
    list_select_related = ("carousel",)
    search_fields = ("alt_text", "carousel__title", "carousel__section_key")
    ordering = ("carousel__section_key", "display_order", "id")

    @admin.display(description="Preview")
    def preview(self, obj):
        if not obj.image:
            return "No image"
        return format_html(
            '<img src="{}" alt="{}" style="height: 60px; width: 108px; object-fit: cover; border-radius: 8px;" />',
            obj.image.url,
            obj.alt_text or obj.carousel,
        )
