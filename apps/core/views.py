from django.views.generic import TemplateView

from apps.portfolio.data import get_featured_portfolio_projects, get_portfolio_projects
from apps.core.models import AboutTeamMember, HeroCarousel, HomeGalleryItem
from apps.core.utils import build_hero_carousel


HOME_MAIN_HERO_FALLBACKS = [
    "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=1800&q=80",
    "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1800&q=80",
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1800&q=80",
    "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1800&q=80",
]
HOME_CTA_HERO_FALLBACKS = [
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1800&q=80",
    "https://images.unsplash.com/photo-1516321134488-95a1c3ee9f9b?auto=format&fit=crop&w=1800&q=80",
    "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1800&q=80",
    "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1800&q=80",
]
CONTACT_HERO_FALLBACKS = [
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1800&q=80",
    "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1800&q=80",
    "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1800&q=80",
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1800&q=80",
]
ABOUT_HERO_IMAGE = (
    "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=1800&q=80"
)
ABOUT_STORY_IMAGE = (
    "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"
)
HOME_PHOTO_GALLERY_FALLBACKS = [
    "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=1200&q=80",
]
HOME_VIDEO_GALLERY_FALLBACKS = [
    "https://images.unsplash.com/photo-1505236858219-8359eb29e329?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1511578314322-379afb476865?auto=format&fit=crop&w=1200&q=80",
]
ABOUT_TEAM_MEMBER_FALLBACKS = [
    {
        "name": "Simon Lado",
        "role": "Lead Photographer",
        "image": "https://images.unsplash.com/photo-1500648767791-00dcc994a43b?auto=format&fit=crop&w=900&q=80",
        "alt_text": "Simon Lado at SudPix",
    },
    {
        "name": "Daniel Ochieng",
        "role": "Creative Director",
        "image": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=900&q=80",
        "alt_text": "Daniel Ochieng at SudPix",
    },
    {
        "name": "Brian Deng",
        "role": "Visual Designer",
        "image": "https://images.unsplash.com/photo-1504593811423-6dd665756598?auto=format&fit=crop&w=900&q=80",
        "alt_text": "Brian Deng at SudPix",
    },
]


def build_media_grid(slug, title, images):
    return [
        {
            "slug": slug,
            "title": f"{title} {index}",
            "image": image,
        }
        for index, image in enumerate(images, start=1)
    ]


def build_admin_home_gallery(section, default_slug, fallback_images, fallback_title):
    gallery_items = list(
        HomeGalleryItem.objects.filter(section=section, is_active=True)
        .order_by("display_order", "id")[:6]
    )

    if gallery_items:
        return [
            {
                "slug": item.project_slug or default_slug,
                "title": item.alt_text or item.title or f"{fallback_title} {index}",
                "image": item.image.url,
            }
            for index, item in enumerate(gallery_items, start=1)
            if item.image
        ]

    return build_media_grid(default_slug, fallback_title, fallback_images)


def build_home_media_gallery():
    projects = {project["slug"]: project for project in get_portfolio_projects()}
    photo_project = projects["wedding-story"]
    video_project = projects["live-event-film"]
    photo_images = [
        photo_project["image"],
        *photo_project["gallery"],
        *HOME_PHOTO_GALLERY_FALLBACKS,
    ]
    video_images = [
        video_project["image"],
        *video_project["gallery"],
        *HOME_VIDEO_GALLERY_FALLBACKS,
    ]

    return {
        "photos": build_admin_home_gallery(
            HomeGalleryItem.Section.PHOTOGRAPHY,
            photo_project["slug"],
            photo_images,
            photo_project["title"],
        ),
        "videos": build_admin_home_gallery(
            HomeGalleryItem.Section.VIDEOGRAPHY,
            video_project["slug"],
            video_images,
            video_project["title"],
        ),
    }


def build_about_team_members():
    team_members = list(
        AboutTeamMember.objects.filter(is_active=True).order_by("display_order", "id")
    )

    if team_members:
        return [
            {
                "name": member.name,
                "role": member.role,
                "image": member.image.url,
                "alt_text": member.alt_text or f"{member.name} at SudPix",
            }
            for member in team_members
            if member.image
        ]

    return ABOUT_TEAM_MEMBER_FALLBACKS


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "hero_stats": [
                    {"value": "250+", "label": "Projects delivered"},
                    {"value": "120+", "label": "Happy clients"},
                    {"value": "24/7", "label": "Client file access"},
                ],
                "hero_file_stream": [
                    {
                        "name": "wedding-highlights.zip",
                        "kind": "Photo set",
                        "size": "324 files",
                        "accent": "amber",
                    },
                    {
                        "name": "event-recap-master.mp4",
                        "kind": "Video cut",
                        "size": "2 min 14 sec",
                        "accent": "orange",
                    },
                    {
                        "name": "launch-brand-kit.pdf",
                        "kind": "Design pack",
                        "size": "18 layouts",
                        "accent": "slate",
                    },
                ],
                "services_preview": [
                    {
                        "title": "Photography",
                        "icon": "📸",
                        "description": "Portraits, events, products",
                        "slug": "photography",
                        "preview_image": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=900&q=80",
                        "asset_count": "320+ stills",
                        "formats": ["RAW", "JPG", "Album"],
                    },
                    {
                        "title": "Videography",
                        "icon": "🎥",
                        "description": "Recaps, reels, branded cuts",
                        "slug": "videography",
                        "preview_image": "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=900&q=80",
                        "asset_count": "4K edits",
                        "formats": ["MP4", "Reels", "Trailer"],
                    },
                    {
                        "title": "Branding",
                        "icon": "✨",
                        "description": "Identity kits, launch assets",
                        "slug": "branding",
                        "preview_image": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=900&q=80",
                        "asset_count": "24+ brand files",
                        "formats": ["Logo", "Deck", "Social"],
                    },
                    {
                        "title": "Graphic Design",
                        "icon": "🎨",
                        "description": "Posters, social packs, print",
                        "slug": "graphic-design",
                        "preview_image": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80",
                        "asset_count": "18+ deliverables",
                        "formats": ["PDF", "PNG", "Print"],
                    },
                ],
                "portfolio_preview": get_featured_portfolio_projects(limit=3),
                "home_media_gallery": build_home_media_gallery(),
                "process_steps": [
                    {"number": "01", "title": "Book", "description": "Choose the service, date, and project direction."},
                    {"number": "02", "title": "Brief", "description": "Confirm the objective, mood, audience, and deliverables."},
                    {"number": "03", "title": "Shoot/Create", "description": "SudPix captures, edits, designs, or builds the brand assets."},
                    {"number": "04", "title": "Preview", "description": "Review protected galleries, video cuts, and design files."},
                    {"number": "05", "title": "Select", "description": "Choose preferred files and give focused feedback."},
                    {"number": "06", "title": "Pay", "description": "Confirm payment status with M-PESA-supported checkout."},
                    {"number": "07", "title": "Download", "description": "Receive final files from the secure client workspace."},
                ],
                "portal_activity": [
                    {"label": "Gallery previews", "value": "Photos, videos, design files"},
                    {"label": "Selection flow", "value": "Tick files and total updates live"},
                    {"label": "Payment gate", "value": "Download opens after checkout"},
                ],
                "testimonials": [
                    {
                        "name": "Amina K.",
                        "role": "Brand Manager",
                        "quote": "SudPix gave our brand launch a polished and premium visual identity. The photography and design quality stood out immediately.",
                    },
                    {
                        "name": "Daniel M.",
                        "role": "Wedding Client",
                        "quote": "The client portal made everything easy. We previewed the photos, selected what we wanted, paid, and downloaded without stress.",
                    },
                    {
                        "name": "Mercy N.",
                        "role": "Corporate Communications Lead",
                        "quote": "Professional, responsive, and creatively sharp. SudPix is the kind of studio you trust with serious projects.",
                    },
                ],
                "home_main_hero": build_hero_carousel(
                    HeroCarousel.Section.HOME_MAIN,
                    HOME_MAIN_HERO_FALLBACKS,
                ),
                "home_cta_hero": build_hero_carousel(
                    HeroCarousel.Section.HOME_CTA,
                    HOME_CTA_HERO_FALLBACKS,
                ),
            }
        )
        return context


class ContactView(TemplateView):
    template_name = "core/contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_hero"] = build_hero_carousel(
            HeroCarousel.Section.CONTACT_MAIN,
            CONTACT_HERO_FALLBACKS,
        )
        return context


class WorkspaceDemoView(TemplateView):
    template_name = "core/workspace_demo.html"


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "about_hero_image": ABOUT_HERO_IMAGE,
                "about_story_image": ABOUT_STORY_IMAGE,
                "about_intro_text": (
                    "SudPix is a creative studio built around premium photography, cinematic videography, "
                    "brand visuals, and polished digital delivery for modern clients."
                ),
                "about_story_points": [
                    "Full-service visual coverage for events, campaigns, and products",
                    "Clean editing, organized file delivery, and secure client access",
                    "Fast communication and studio workflows that stay easy to follow",
                    "Creative direction shaped around premium presentation and final use",
                ],
                "about_work_intro": {
                    "title": "How we work?",
                    "lead": (
                        "SudPix keeps every project visual, organized, and easy to follow from the first brief "
                        "to the final downloadable files."
                    ),
                    "description": (
                        "Our workflow is built for modern media clients who want premium output without a confusing "
                        "back-and-forth process. We guide the direction, schedule the production, and prepare the "
                        "final files inside a clean delivery system."
                    ),
                },
                "about_work_steps": [
                    {
                        "badge": "01",
                        "title": "Tell us about your project",
                        "description": "Share the event, campaign, or brand goal so we can shape the right creative direction.",
                    },
                    {
                        "badge": "02",
                        "title": "We schedule the shoot",
                        "description": "SudPix aligns dates, coverage needs, and production details before any capture starts.",
                    },
                    {
                        "badge": "03",
                        "title": "We prepare delivery",
                        "description": "After editing, we organize the files into a polished client-ready gallery and download flow.",
                    },
                ],
                "about_team_members": build_about_team_members(),
                "about_process_steps": [
                    {
                        "number": "01",
                        "title": "Discussion",
                        "description": "We align on the goal, audience, timing, and visual mood before any production starts.",
                    },
                    {
                        "number": "02",
                        "title": "Strategy",
                        "description": "SudPix maps the right service mix, coverage format, and file output for the project.",
                    },
                    {
                        "number": "03",
                        "title": "Core Concept",
                        "description": "We shape the creative direction, styling cues, and story structure for the final work.",
                    },
                    {
                        "number": "04",
                        "title": "Feasibility",
                        "description": "The team locks locations, timing, asset needs, and delivery expectations with clarity.",
                    },
                    {
                        "number": "05",
                        "title": "Execution",
                        "description": "Production and editing move forward with a strong focus on premium media quality.",
                    },
                    {
                        "number": "06",
                        "title": "Follow Up",
                        "description": "Clients preview, select, pay, and download through the SudPix delivery workflow.",
                    },
                ],
            }
        )
        return context


class FAQView(TemplateView):
    template_name = "core/faq.html"
