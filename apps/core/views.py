from django.views.generic import TemplateView

from apps.portfolio.data import get_featured_portfolio_projects, get_portfolio_projects
from apps.core.models import HeroCarousel
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


def build_home_media_gallery():
    projects = {project["slug"]: project for project in get_portfolio_projects()}
    photo_project = projects["wedding-story"]
    video_project = projects["live-event-film"]

    return {
        "photos": [
            {
                "slug": photo_project["slug"],
                "image": photo_project["image"],
                "title": "Couple portraits",
                "collection": photo_project["title"],
                "caption": "Refined wedding portraits built for timeless gallery delivery.",
            },
            {
                "slug": photo_project["slug"],
                "image": photo_project["gallery"][0],
                "title": "Ceremony details",
                "collection": photo_project["title"],
                "caption": "Clean stills shaped around emotion, style, and event atmosphere.",
            },
            {
                "slug": photo_project["slug"],
                "image": photo_project["gallery"][1],
                "title": "Reception moments",
                "collection": photo_project["title"],
                "caption": "Guest reactions, decor, and movement captured as polished frames.",
            },
            {
                "slug": photo_project["slug"],
                "image": photo_project["gallery"][2],
                "title": "Golden-hour edit",
                "collection": photo_project["title"],
                "caption": "Warm editorial light and premium finishing across the final selects.",
            },
        ],
        "videos": [
            {
                "slug": video_project["slug"],
                "image": video_project["image"],
                "title": "Main recap cut",
                "eyebrow": "Videography",
                "runtime": video_project["metrics"][1]["value"],
                "caption": "The hero event film shaped for premium post-event release and promotion.",
            },
            {
                "slug": video_project["slug"],
                "image": video_project["gallery"][0],
                "title": "Opening energy",
                "eyebrow": "Event coverage",
                "runtime": "45 sec",
                "caption": "Fast, cinematic coverage of the first crowd and stage moments.",
            },
            {
                "slug": video_project["slug"],
                "image": video_project["gallery"][1],
                "title": "Audience reactions",
                "eyebrow": "Highlight clip",
                "runtime": "30 sec",
                "caption": "Short-form social-ready moments captured for reels and recap cutdowns.",
            },
        ],
    }


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
                    {"number": "01", "title": "Choose a service", "description": "Pick photo, video, branding, or design."},
                    {"number": "02", "title": "Book your slot", "description": "Send the date and creative brief."},
                    {"number": "03", "title": "Capture or design", "description": "SudPix creates the working files."},
                    {"number": "04", "title": "Preview assets", "description": "Open the gallery or project files online."},
                    {"number": "05", "title": "Pay and download", "description": "Unlock the selected files instantly."},
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
