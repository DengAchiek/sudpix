from django.views.generic import TemplateView


class PortfolioListView(TemplateView):
    template_name = "portfolio/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = [
            {
                "title": "Wedding Story",
                "category": "Photography",
                "summary": "Elegant ceremony coverage, intimate portraits, and a complete wedding-day story.",
                "image": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=80",
            },
            {
                "title": "Corporate Campaign",
                "category": "Branding",
                "summary": "A premium identity refresh and rollout kit for a growing business audience.",
                "image": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
            },
            {
                "title": "Live Event Film",
                "category": "Videography",
                "summary": "Fast-turnaround event recap production tailored for digital promotion.",
                "image": "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=1200&q=80",
            },
            {
                "title": "Launch Graphics Suite",
                "category": "Graphic Design",
                "summary": "Campaign posters, motion-ready social assets, and event collateral in one system.",
                "image": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1200&q=80",
            },
        ]
        context["portfolio_stats"] = [
            {"label": "Projects delivered", "value": "250+"},
            {"label": "Creative categories", "value": "4"},
            {"label": "Average turnaround", "value": "7 days"},
        ]
        return context
