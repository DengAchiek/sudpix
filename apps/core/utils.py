from decimal import Decimal, ROUND_HALF_UP

from .models import HeroCarousel


def format_currency(value):
    amount = Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if amount == amount.to_integral():
        return f"KES {amount:,.0f}"

    return f"KES {amount:,.2f}"


HERO_CAROUSEL_STEP_SECONDS = 6


def build_hero_carousel(section_key, fallback_urls):
    fallback_slide_urls = [url for url in fallback_urls if url]
    carousel = (
        HeroCarousel.objects.filter(section_key=section_key, is_active=True)
        .prefetch_related("slides")
        .first()
    )

    slide_urls = []
    if carousel:
        slide_urls = [slide.image.url for slide in carousel.slides.all() if slide.image]

    slide_urls = (slide_urls or fallback_slide_urls)[:4]
    duration = max(len(slide_urls), 1) * HERO_CAROUSEL_STEP_SECONDS

    return {
        "slides": [
            {
                "url": url,
                "delay": index * HERO_CAROUSEL_STEP_SECONDS,
            }
            for index, url in enumerate(slide_urls)
        ],
        "duration": duration,
        "is_static": len(slide_urls) <= 1,
    }
