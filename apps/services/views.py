from django.views.generic import TemplateView


class ServiceListView(TemplateView):
    template_name = "services/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "service_categories": [
                    "Photography",
                    "Videography",
                    "Branding",
                    "Graphic Design",
                ],
                "featured_service": {
                    "title": "Photography Services",
                    "description": "Professional photography for events, products, portraits, and campaigns.",
                    "included": [
                        "Edited high-resolution files",
                        "Online preview gallery",
                        "Organized client folders",
                        "Download-ready delivery",
                    ],
                    "best_for": [
                        "Weddings and events",
                        "Product shoots",
                        "Corporate campaigns",
                        "Personal portraits",
                    ],
                },
                "packages": [
                    {
                        "name": "Starter Shoot",
                        "price": "KES 12,000",
                        "description": "Best for portraits, product mini shoots, and quick sessions.",
                    },
                    {
                        "name": "Business Package",
                        "price": "KES 35,000",
                        "description": "Designed for campaigns, corporate shoots, and structured visual content.",
                    },
                    {
                        "name": "Enterprise / Event",
                        "price": "Custom Quote",
                        "description": "Full-day or multi-day event coverage with custom requirements.",
                    },
                ],
            }
        )
        return context
