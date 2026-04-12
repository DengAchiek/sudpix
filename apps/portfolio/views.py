from django.http import Http404
from django.views.generic import TemplateView

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
        return context
