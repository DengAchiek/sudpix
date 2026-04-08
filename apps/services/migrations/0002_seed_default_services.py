from django.db import migrations


DEFAULT_SERVICES = [
    {
        "slug": "photography",
        "name": "Photography",
        "badge": "Photography Services",
        "heading": "Professional photography for events, products, portraits, and campaigns",
        "description": (
            "We create polished photo content that helps businesses market better, "
            "individuals preserve moments, and brands present themselves with confidence."
        ),
        "included_items": "\n".join(
            [
                "Edited high-resolution files",
                "Online preview gallery",
                "Organized client folders",
                "Download-ready delivery",
            ]
        ),
        "best_for_items": "\n".join(
            [
                "Weddings and events",
                "Product shoots",
                "Corporate campaigns",
                "Personal portraits",
            ]
        ),
        "packages_heading": "Photography Packages",
        "book_label": "Book Photography",
        "booking_service": "Photography",
        "teaser": "Portraits, events, product shoots, and visual campaigns with polished delivery.",
        "icon": "📸",
        "display_order": 1,
        "packages": [
            {
                "name": "Starter Shoot",
                "price_label": "KES 12,000",
                "description": "Best for portraits, product mini shoots, and quick sessions.",
                "highlighted": False,
                "display_order": 1,
            },
            {
                "name": "Business Package",
                "price_label": "KES 35,000",
                "description": "Designed for campaigns, corporate shoots, and structured visual content.",
                "highlighted": True,
                "display_order": 2,
            },
            {
                "name": "Enterprise / Event",
                "price_label": "Custom Quote",
                "description": "Full-day or multi-day event coverage with custom requirements.",
                "highlighted": False,
                "display_order": 3,
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
        "included_items": "\n".join(
            [
                "Edited highlight or feature video",
                "Audio cleanup and pacing polish",
                "Social cutdowns for promo use",
                "Ready-to-share delivery formats",
            ]
        ),
        "best_for_items": "\n".join(
            [
                "Event recap films",
                "Brand stories and launches",
                "Interviews and testimonials",
                "Social media promo content",
            ]
        ),
        "packages_heading": "Videography Packages",
        "book_label": "Book Videography",
        "booking_service": "Videography",
        "teaser": "Recap films, campaign videos, interviews, and branded motion content.",
        "icon": "🎥",
        "display_order": 2,
        "packages": [
            {
                "name": "Highlight Reel",
                "price_label": "KES 18,000",
                "description": "A short polished recap for launches, parties, and intimate events.",
                "highlighted": False,
                "display_order": 1,
            },
            {
                "name": "Brand Story Package",
                "price_label": "KES 45,000",
                "description": "Ideal for campaigns, interviews, and structured marketing videos.",
                "highlighted": True,
                "display_order": 2,
            },
            {
                "name": "Full Event Coverage",
                "price_label": "Custom Quote",
                "description": "Multi-camera or extended event filming with custom edit deliverables.",
                "highlighted": False,
                "display_order": 3,
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
        "included_items": "\n".join(
            [
                "Logo and identity direction",
                "Brand color and typography system",
                "Core social and marketing assets",
                "Guided rollout recommendations",
            ]
        ),
        "best_for_items": "\n".join(
            [
                "New business launches",
                "Rebrands and refreshes",
                "Campaign identity systems",
                "Growing service businesses",
            ]
        ),
        "packages_heading": "Branding Packages",
        "book_label": "Book Branding",
        "booking_service": "Branding",
        "teaser": "Identity systems, launch visuals, and consistent brand rollouts.",
        "icon": "✨",
        "display_order": 3,
        "packages": [
            {
                "name": "Identity Starter",
                "price_label": "KES 20,000",
                "description": "Perfect for founders who need a confident visual identity foundation.",
                "highlighted": False,
                "display_order": 1,
            },
            {
                "name": "Brand System",
                "price_label": "KES 55,000",
                "description": "A fuller identity package with rollout assets for marketing consistency.",
                "highlighted": True,
                "display_order": 2,
            },
            {
                "name": "Campaign / Rebrand",
                "price_label": "Custom Quote",
                "description": "Built for complex rebrands, activations, and audience-facing campaigns.",
                "highlighted": False,
                "display_order": 3,
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
        "included_items": "\n".join(
            [
                "Social and campaign graphics",
                "Print-ready poster and flyer layouts",
                "Presentation and promo assets",
                "Organized export delivery",
            ]
        ),
        "best_for_items": "\n".join(
            [
                "Event promotions",
                "Marketing campaigns",
                "Sales decks and presentations",
                "Retail and product launches",
            ]
        ),
        "packages_heading": "Graphic Design Packages",
        "book_label": "Book Graphic Design",
        "booking_service": "Graphic Design",
        "teaser": "Posters, social creatives, sales assets, and polished campaign graphics.",
        "icon": "🎨",
        "display_order": 4,
        "packages": [
            {
                "name": "Promo Kit",
                "price_label": "KES 8,000",
                "description": "A focused set of campaign or event graphics for quick rollout.",
                "highlighted": False,
                "display_order": 1,
            },
            {
                "name": "Marketing Suite",
                "price_label": "KES 22,000",
                "description": "Best for brands that need a coordinated batch of polished design assets.",
                "highlighted": True,
                "display_order": 2,
            },
            {
                "name": "Ongoing Design Support",
                "price_label": "Custom Quote",
                "description": "Flexible monthly or campaign-based design support built around your needs.",
                "highlighted": False,
                "display_order": 3,
            },
        ],
    },
]


def seed_services(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    ServicePackage = apps.get_model("services", "ServicePackage")

    for service_data in DEFAULT_SERVICES:
        packages = service_data["packages"]
        service_defaults = {key: value for key, value in service_data.items() if key != "packages"}
        service, _ = Service.objects.update_or_create(
            slug=service_data["slug"],
            defaults=service_defaults,
        )

        existing_names = []
        for package_data in packages:
            package, _ = ServicePackage.objects.update_or_create(
                service=service,
                name=package_data["name"],
                defaults=package_data,
            )
            existing_names.append(package.name)

        ServicePackage.objects.filter(service=service).exclude(name__in=existing_names).delete()


def unseed_services(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    Service.objects.filter(slug__in=[service["slug"] for service in DEFAULT_SERVICES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_services, unseed_services),
    ]
