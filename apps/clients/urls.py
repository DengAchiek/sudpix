from django.urls import path

from .views import (
    AddToCartView,
    AddProjectFeedbackView,
    ApproveProjectView,
    CartView,
    CheckoutView,
    DashboardView,
    DownloadAssetView,
    DownloadsView,
    FilesView,
    PaymentProcessingView,
    PaymentStatusView,
    PaymentsView,
    PreviewAssetView,
    ProjectDetailView,
    ProjectsView,
    RemoveFromCartView,
    RequestProjectRevisionView,
    RetryPaymentPromptView,
    UpdateProjectBriefView,
)

app_name = "client"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("projects/", ProjectsView.as_view(), name="projects"),
    path("projects/<slug:slug>/", ProjectDetailView.as_view(), name="project_detail"),
    path("projects/<slug:slug>/brief/", UpdateProjectBriefView.as_view(), name="update_brief"),
    path("projects/<slug:slug>/feedback/", AddProjectFeedbackView.as_view(), name="add_feedback"),
    path("projects/<slug:slug>/revisions/", RequestProjectRevisionView.as_view(), name="request_revision"),
    path("projects/<slug:slug>/approval/", ApproveProjectView.as_view(), name="approve_project"),
    path("files/", FilesView.as_view(), name="files"),
    path("files/<int:file_id>/preview/", PreviewAssetView.as_view(), name="preview_file"),
    path("files/<int:file_id>/download/", DownloadAssetView.as_view(), name="download_file"),
    path("files/<int:file_id>/select/", AddToCartView.as_view(), name="select_file"),
    path("files/<int:file_id>/remove/", RemoveFromCartView.as_view(), name="remove_file"),
    path("cart/", CartView.as_view(), name="cart"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("payments/", PaymentsView.as_view(), name="payments"),
    path("payments/<int:payment_id>/processing/", PaymentProcessingView.as_view(), name="payment_processing"),
    path("payments/<int:payment_id>/status/", PaymentStatusView.as_view(), name="payment_status"),
    path("payments/<int:payment_id>/retry/", RetryPaymentPromptView.as_view(), name="retry_payment"),
    path("downloads/", DownloadsView.as_view(), name="downloads"),
]
