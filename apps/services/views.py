from django.http import Http404
from django.views.generic import TemplateView

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

        context.update(
            {
                "service_categories": services,
                "active_service": active_service,
                "related_services": [
                    service for service in services if active_service and service.slug != active_service.slug
                ] if active_service else [],
            }
        )
        return context
