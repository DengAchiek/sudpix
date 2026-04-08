from django.urls import path

from .views import PortfolioListView

app_name = "portfolio"

urlpatterns = [
    path("", PortfolioListView.as_view(), name="list"),
]
