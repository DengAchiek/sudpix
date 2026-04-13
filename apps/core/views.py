from django.views.generic import TemplateView

from apps.portfolio.data import get_featured_portfolio_projects


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
            }
        )
        return context


class ContactView(TemplateView):
    template_name = "core/contact.html"


class AboutView(TemplateView):
    template_name = "core/about.html"


class FAQView(TemplateView):
    template_name = "core/faq.html"
