from django.http import Http404
from django.views.generic import TemplateView

from apps.core.models import HeroCarousel
from apps.core.utils import build_hero_carousel

from .models import Service


class ServiceListView(TemplateView):
    template_name = "services/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        services = list(
            Service.objects.filter(is_active=True)
            .prefetch_related("packages")
            .order_by("display_order", "name")
        )
        active_slug = self.kwargs.get("service_slug")
        active_service = None

        if active_slug:
            active_service = next((service for service in services if service.slug == active_slug), None)
        elif services:
            active_service = services[0]

        if active_slug and active_service is None:
            raise Http404("Service not found.")

        active_primary_image = None
        if active_service:
            active_primary_image = active_service.showcase_media.get("poster") or active_service.showcase_media.get("url")

        context.update(
            {
                "service_categories": services,
                "active_service": active_service,
                "related_services": [
                    service for service in services if active_service and service.slug != active_service.slug
                ] if active_service else [],
                "services_active_hero": build_hero_carousel(
                    HeroCarousel.Section.SERVICES_MAIN,
                    [
                        active_primary_image,
                        "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1800&q=80",
                        "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=1800&q=80",
                        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1800&q=80",
                    ],
                ) if active_service else None,
                "services_empty_hero": build_hero_carousel(
                    HeroCarousel.Section.SERVICES_EMPTY,
                    [
                        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1800&q=80",
                        "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1800&q=80",
                        "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=1800&q=80",
                        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1800&q=80",
                    ],
                ),
            }
        )
        return context
