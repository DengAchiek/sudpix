from django.http import Http404
from django.views.generic import TemplateView

from apps.core.models import HeroCarousel
from apps.core.utils import build_hero_carousel

from .data import get_portfolio_project, get_portfolio_projects


class PortfolioListView(TemplateView):
    template_name = "portfolio/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = get_portfolio_projects()
        context["portfolio_stats"] = [
            {"label": "Projects delivered", "value": "250+"},
            {"label": "Creative categories", "value": "4"},
            {"label": "Average turnaround", "value": "7 days"},
        ]
        context["portfolio_list_hero"] = build_hero_carousel(
            HeroCarousel.Section.PORTFOLIO_LIST,
            [
                "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1800&q=80",
                "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=1800&q=80",
                "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1800&q=80",
                "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1800&q=80",
            ],
        )
        return context


class PortfolioDetailView(TemplateView):
    template_name = "portfolio/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_portfolio_project(self.kwargs["project_slug"])

        if project is None:
            raise Http404("Portfolio project not found.")

        context["project"] = project
        context["related_projects"] = [
            item for item in get_portfolio_projects() if item["slug"] != project["slug"]
        ][:3]
        context["portfolio_detail_hero"] = build_hero_carousel(
            HeroCarousel.Section.PORTFOLIO_DETAIL,
            [project["image"], *project["gallery"][:3]],
        )
        return context
