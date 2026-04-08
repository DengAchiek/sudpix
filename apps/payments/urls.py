from django.urls import path

from .views import MpesaCallbackView

app_name = "payments"

urlpatterns = [
    path("mpesa/callback/", MpesaCallbackView.as_view(), name="mpesa_callback"),
]
