from django.http import Http404
from django.views.generic import TemplateView

from apps.core.models import HeroCarousel
from apps.core.utils import build_hero_carousel

from .data import get_portfolio_project, get_portfolio_projects


class PortfolioListView(TemplateView):
    template_name = "portfolio/list.html"

    def build_gallery_tiles(self, projects):
        curated_images = []

        for project in projects:
            curated_images.append(
                {
                    "slug": project["slug"],
                    "title": project["title"],
                    "category": project["category"],
                    "image": project["image"],
                    "tag": project["delivery_mode"],
                }
            )

        for project in projects:
            for image in project["gallery"][:1]:
                curated_images.append(
                    {
                        "slug": project["slug"],
                        "title": project["title"],
                        "category": project["category"],
                        "image": image,
                        "tag": project["formats"][0],
                    }
                )

        return curated_images[:6]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = get_portfolio_projects()
        context["projects"] = projects
        context["portfolio_gallery_tiles"] = self.build_gallery_tiles(projects)
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
