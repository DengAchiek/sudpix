from django.views.generic import TemplateView


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
                "services_preview": [
                    {
                        "title": "Photography",
                        "icon": "📸",
                        "description": "Event, lifestyle, product, corporate, and portrait photography captured with precision and style.",
                    },
                    {
                        "title": "Videography",
                        "icon": "🎥",
                        "description": "Cinematic event coverage, promotional videos, interviews, social clips, and branded video content.",
                    },
                    {
                        "title": "Branding",
                        "icon": "✨",
                        "description": "Build a memorable identity with logo systems, brand strategy, social assets, and visual guidelines.",
                    },
                    {
                        "title": "Graphic Design",
                        "icon": "🎨",
                        "description": "Professional flyers, social media graphics, marketing designs, print layouts, and digital campaigns.",
                    },
                ],
                "portfolio_preview": [
                    {
                        "title": "Wedding Story",
                        "category": "Photography",
                        "description": "Elegant wedding coverage with cinematic couple portraits and complete event storytelling.",
                        "image": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=80",
                    },
                    {
                        "title": "Corporate Campaign",
                        "category": "Branding",
                        "description": "Professional visual identity and campaign assets built for a growing corporate brand.",
                        "image": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
                    },
                    {
                        "title": "Live Event Film",
                        "category": "Videography",
                        "description": "A polished event recap film designed for digital promotion and audience engagement.",
                        "image": "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=1200&q=80",
                    },
                ],
                "process_steps": [
                    {"number": "01", "title": "Choose a service", "description": "Select photography, videography, branding, or design based on your needs."},
                    {"number": "02", "title": "Book your project", "description": "Submit your brief, event details, location, and preferred schedule online."},
                    {"number": "03", "title": "We create", "description": "Our team handles shooting, editing, design, and project delivery professionally."},
                    {"number": "04", "title": "Preview your files", "description": "Access your secure client portal to preview available photos and videos."},
                    {"number": "05", "title": "Pay and download", "description": "Select your files, see the total amount instantly, pay securely, and download."},
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
