from django.urls import path

from .views import PortfolioDetailView, PortfolioListView

app_name = "portfolio"

urlpatterns = [
    path("", PortfolioListView.as_view(), name="list"),
    path("<slug:project_slug>/", PortfolioDetailView.as_view(), name="detail"),
]
