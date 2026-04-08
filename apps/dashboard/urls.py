from django.urls import path

from .views import StaffDashboardView

app_name = "dashboard"

urlpatterns = [
    path("", StaffDashboardView.as_view(), name="home"),
]
