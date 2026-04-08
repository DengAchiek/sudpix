from django.http import Http404
from django.views.generic import TemplateView


SERVICE_DATA = [
    {
        "slug": "photography",
        "name": "Photography",
        "badge": "Photography Services",
        "heading": "Professional photography for events, products, portraits, and campaigns",
        "description": (
            "We create polished photo content that helps businesses market better, "
            "individuals preserve moments, and brands present themselves with confidence."
        ),
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
        "packages_heading": "Photography Packages",
        "book_label": "Book Photography",
        "book_service": "Photography",
        "teaser": "Portraits, events, product shoots, and visual campaigns with polished delivery.",
        "icon": "📸",
        "packages": [
            {
                "name": "Starter Shoot",
                "price": "KES 12,000",
                "description": "Best for portraits, product mini shoots, and quick sessions.",
                "highlighted": False,
            },
            {
                "name": "Business Package",
                "price": "KES 35,000",
                "description": "Designed for campaigns, corporate shoots, and structured visual content.",
                "highlighted": True,
            },
            {
                "name": "Enterprise / Event",
                "price": "Custom Quote",
                "description": "Full-day or multi-day event coverage with custom requirements.",
                "highlighted": False,
            },
        ],
    },
    {
        "slug": "videography",
        "name": "Videography",
        "badge": "Videography Services",
        "heading": "Cinematic videography for launches, events, interviews, and branded storytelling",
        "description": (
            "SudPix produces story-led video content designed to capture atmosphere, "
            "communicate brand value, and give every campaign a polished moving-image presence."
        ),
        "included": [
            "Edited highlight or feature video",
            "Audio cleanup and pacing polish",
            "Social cutdowns for promo use",
            "Ready-to-share delivery formats",
        ],
        "best_for": [
            "Event recap films",
            "Brand stories and launches",
            "Interviews and testimonials",
            "Social media promo content",
        ],
        "packages_heading": "Videography Packages",
        "book_label": "Book Videography",
        "book_service": "Videography",
        "teaser": "Recap films, campaign videos, interviews, and branded motion content.",
        "icon": "🎥",
        "packages": [
            {
                "name": "Highlight Reel",
                "price": "KES 18,000",
                "description": "A short polished recap for launches, parties, and intimate events.",
                "highlighted": False,
            },
            {
                "name": "Brand Story Package",
                "price": "KES 45,000",
                "description": "Ideal for campaigns, interviews, and structured marketing videos.",
                "highlighted": True,
            },
            {
                "name": "Full Event Coverage",
                "price": "Custom Quote",
                "description": "Multi-camera or extended event filming with custom edit deliverables.",
                "highlighted": False,
            },
        ],
    },
    {
        "slug": "branding",
        "name": "Branding",
        "badge": "Branding Services",
        "heading": "Strategic branding systems that help businesses look clear, premium, and memorable",
        "description": (
            "We shape cohesive identities that align visuals, tone, and rollout assets so your "
            "brand shows up consistently across every client touchpoint."
        ),
        "included": [
            "Logo and identity direction",
            "Brand color and typography system",
            "Core social and marketing assets",
            "Guided rollout recommendations",
        ],
        "best_for": [
            "New business launches",
            "Rebrands and refreshes",
            "Campaign identity systems",
            "Growing service businesses",
        ],
        "packages_heading": "Branding Packages",
        "book_label": "Book Branding",
        "book_service": "Branding",
        "teaser": "Identity systems, launch visuals, and consistent brand rollouts.",
        "icon": "✨",
        "packages": [
            {
                "name": "Identity Starter",
                "price": "KES 20,000",
                "description": "Perfect for founders who need a confident visual identity foundation.",
                "highlighted": False,
            },
            {
                "name": "Brand System",
                "price": "KES 55,000",
                "description": "A fuller identity package with rollout assets for marketing consistency.",
                "highlighted": True,
            },
            {
                "name": "Campaign / Rebrand",
                "price": "Custom Quote",
                "description": "Built for complex rebrands, activations, and audience-facing campaigns.",
                "highlighted": False,
            },
        ],
    },
    {
        "slug": "graphic-design",
        "name": "Graphic Design",
        "badge": "Graphic Design Services",
        "heading": "Design support for marketing, promotions, launches, and everyday brand communication",
        "description": (
            "From social graphics to print-ready collateral, we create design assets that help "
            "your message stay sharp, consistent, and easy to recognize."
        ),
        "included": [
            "Social and campaign graphics",
            "Print-ready poster and flyer layouts",
            "Presentation and promo assets",
            "Organized export delivery",
        ],
        "best_for": [
            "Event promotions",
            "Marketing campaigns",
            "Sales decks and presentations",
            "Retail and product launches",
        ],
        "packages_heading": "Graphic Design Packages",
        "book_label": "Book Graphic Design",
        "book_service": "Graphic Design",
        "teaser": "Posters, social creatives, sales assets, and polished campaign graphics.",
        "icon": "🎨",
        "packages": [
            {
                "name": "Promo Kit",
                "price": "KES 8,000",
                "description": "A focused set of campaign or event graphics for quick rollout.",
                "highlighted": False,
            },
            {
                "name": "Marketing Suite",
                "price": "KES 22,000",
                "description": "Best for brands that need a coordinated batch of polished design assets.",
                "highlighted": True,
            },
            {
                "name": "Ongoing Design Support",
                "price": "Custom Quote",
                "description": "Flexible monthly or campaign-based design support built around your needs.",
                "highlighted": False,
            },
        ],
    },
]

SERVICE_LOOKUP = {service["slug"]: service for service in SERVICE_DATA}


class ServiceListView(TemplateView):
    template_name = "services/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_slug = self.kwargs.get("service_slug") or SERVICE_DATA[0]["slug"]
        active_service = SERVICE_LOOKUP.get(active_slug)
        if active_service is None:
            raise Http404("Service not found.")

        context.update(
            {
                "service_categories": SERVICE_DATA,
                "active_service": active_service,
                "related_services": [
                    service for service in SERVICE_DATA if service["slug"] != active_service["slug"]
                ],
            }
        )
        return context
